"""Local Supabase-compatible API bridge for the Oracle PostgreSQL primary.

Only enabled on the Oracle API process with DLR_LOCAL_SUPABASE_PROXY_ENABLED=true.
The raw database, PostgREST, and GoTrue listeners remain bound to loopback.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import error as urlerror, parse, request as urlrequest
from uuid import UUID

from fastapi import FastAPI, Request, Response
from starlette.concurrency import run_in_threadpool

_AUTH_ORIGIN = "http://127.0.0.1:9999"
_REST_ORIGIN = "http://127.0.0.1:3001"
_HOP_HEADERS = {
    "host", "content-length", "connection", "transfer-encoding", "keep-alive",
    "proxy-authenticate", "proxy-authorization", "te", "trailer", "upgrade",
    "accept-encoding",
}
_RESPONSE_HEADERS = {
    "content-type", "content-range", "content-location", "content-disposition",
    "cache-control", "etag", "last-modified", "location", "preference-applied",
    "vary", "accept-ranges", "range-unit", "www-authenticate", "content-profile",
    "set-cookie",
}


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _service_role_token() -> str:
    secret_path = Path(os.environ.get(
        "DLR_LOCAL_JWT_SECRET_FILE",
        "/home/prashant/.config/dlr/local-platform/jwt-secret",
    ))
    secret = secret_path.read_text(encoding="utf-8").strip().encode("utf-8")
    if len(secret) < 32:
        raise RuntimeError("Local JWT signing secret is missing or too short")
    now = int(time.time())
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    claims = _b64url(json.dumps({
        "iss": "supabase",
        "aud": "authenticated",
        "role": "service_role",
        "sub": "00000000-0000-0000-0000-000000000000",
        "iat": now,
        "exp": now + 300,
    }, separators=(",", ":")).encode())
    unsigned = f"{header}.{claims}"
    signature = _b64url(hmac.new(secret, unsigned.encode("ascii"), hashlib.sha256).digest())
    return f"{unsigned}.{signature}"


def _http_call(
    base: str,
    path: str,
    *,
    method: str = "GET",
    body: dict[str, object] | None = None,
    bearer: str | None = None,
    extra_headers: dict[str, str] | None = None,
    timeout: int = 45,
) -> tuple[int, bytes, dict[str, str]]:
    target = base.rstrip("/") + (path if path.startswith("/") else "/" + path)
    payload = None if body is None else json.dumps(body, separators=(",", ":")).encode("utf-8")
    headers = {"Accept": "application/json"}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if extra_headers:
        headers.update(extra_headers)
    req = urlrequest.Request(target, data=payload, headers=headers, method=method)
    try:
        with urlrequest.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            return int(resp.status), resp.read(), {k.lower(): v for k, v in resp.headers.items()}
    except urlerror.HTTPError as exc:
        return int(exc.code), exc.read(), {k.lower(): v for k, v in exc.headers.items()}
    except (urlerror.URLError, TimeoutError, OSError):
        return 502, b'{"error":"local backend unavailable"}', {"content-type": "application/json"}


def _json_body(raw: bytes) -> object:
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def _service_rest(method: str, path: str, body: dict[str, object] | None = None,
                  *, prefer: str | None = None) -> tuple[int, object, bytes]:
    headers = {"Prefer": prefer} if prefer else None
    code, raw, _ = _http_call(_REST_ORIGIN, path, method=method, body=body,
                              bearer=_service_role_token(), extra_headers=headers)
    return code, _json_body(raw), raw


def _auth_admin(method: str, path: str, body: dict[str, object] | None = None) -> tuple[int, object, bytes]:
    code, raw, _ = _http_call(_AUTH_ORIGIN, path, method=method, body=body,
                              bearer=_service_role_token())
    return code, _json_body(raw), raw


def _cors_origin(request: Request) -> str | None:
    origin = request.headers.get("origin", "").strip()
    if not origin:
        return None
    allowed = {item.strip().rstrip("/") for item in os.environ.get("DLR_LOCAL_CORS_ORIGINS", "").split(",") if item.strip()}
    for key in ("AUTH_APP_ORIGIN", "AUTH_REDIRECT_URL"):
        value = os.environ.get(key, "").strip()
        if value:
            parsed = parse.urlsplit(value)
            if parsed.scheme and parsed.netloc:
                allowed.add(f"{parsed.scheme}://{parsed.netloc}")
    allowed.update({"https://eletters.vercel.app", "https://digital-letter-registry.vercel.app"})
    return origin if origin.rstrip("/") in allowed else None


def _cors_headers(request: Request) -> dict[str, str]:
    origin = _cors_origin(request)
    if not origin:
        return {}
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS,HEAD",
        "Access-Control-Allow-Headers": "Authorization, apikey, Content-Type, Prefer, Range, Range-Unit, Accept, Accept-Profile, Content-Profile, X-Client-Info, X-Supabase-Api-Version, Cache-Control",
        "Access-Control-Expose-Headers": "Content-Range, Range-Unit, Preference-Applied, Content-Location, ETag",
        "Access-Control-Max-Age": "86400",
        "Vary": "Origin",
    }


async def _forward(request: Request, backend: str, path: str) -> Response:
    cors = _cors_headers(request)
    if request.method == "OPTIONS":
        if request.headers.get("origin") and not cors:
            return Response(status_code=403, headers={"Cache-Control": "no-store"})
        return Response(status_code=204, headers={**cors, "Cache-Control": "no-store"})
    query = request.url.query
    target_path = "/" + path.lstrip("/") if path else "/"
    target = backend.rstrip("/") + target_path + ("?" + query if query else "")
    body = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() not in _HOP_HEADERS}
    method = request.method.upper()
    if method in {"GET", "HEAD"}:
        body = b""
    code, raw, upstream_headers = await run_in_threadpool(
        _http_raw, target, method, body if body else None, headers
    )
    response_headers = {k: v for k, v in upstream_headers.items() if k in _RESPONSE_HEADERS}
    response_headers.update(cors)
    response_headers.setdefault("Cache-Control", "private, no-store" if path.startswith(("user", "token", "logout", "admin/")) else "no-store")
    return Response(content=raw, status_code=code, headers=response_headers)


def _http_raw(target: str, method: str, body: bytes | None, headers: dict[str, str]) -> tuple[int, bytes, dict[str, str]]:
    req = urlrequest.Request(target, data=body, headers=headers, method=method)
    try:
        with urlrequest.urlopen(req, timeout=120) as resp:  # noqa: S310
            return int(resp.status), resp.read(), {k.lower(): v for k, v in resp.headers.items()}
    except urlerror.HTTPError as exc:
        return int(exc.code), exc.read(), {k.lower(): v for k, v in exc.headers.items()}
    except (urlerror.URLError, TimeoutError, OSError):
        return 502, b'{"message":"local backend unavailable"}', {"content-type": "application/json"}


def _bearer(request: Request) -> str | None:
    value = request.headers.get("authorization", "").strip()
    if value.lower().startswith("bearer "):
        return value[7:].strip()
    return None


def _error(message: str, status_code: int, request: Request) -> Response:
    return Response(content=json.dumps({"error": message}), status_code=status_code,
                    media_type="application/json", headers={"Cache-Control": "no-store", **_cors_headers(request)})


def _membership_rows(archive_id: str, *, user_id: str | None = None,
                     role: str | None = None, status: str | None = None) -> tuple[int, list[dict[str, object]]]:
    params: dict[str, str] = {"select": "user_id,role,status", "archive_id": f"eq.{archive_id}", "limit": "1000"}
    if user_id: params["user_id"] = f"eq.{user_id}"
    if role: params["role"] = f"eq.{role}"
    if status: params["status"] = f"eq.{status}"
    code, body, _ = _service_rest("GET", "/archive_members?" + parse.urlencode(params))
    return code, body if isinstance(body, list) else []


def _local_admin_user_account(request: Request) -> Response:
    if request.method != "POST":
        return _error("method not allowed", 405, request)
    bearer = _bearer(request)
    if not bearer:
        return _error("authentication required", 401, request)
    try:
        body = json.loads(request._body.decode("utf-8"))  # body is set by the route handler
    except Exception:
        return _error("invalid request", 400, request)
    action = str(body.get("action") or "").strip()
    archive_id = str(body.get("archive_id") or "").strip()
    target_id = str(body.get("user_id") or "").strip()
    password = str(body.get("password") or "")
    try:
        configured_archive = str(UUID(os.environ.get("DLR_ARCHIVE_ID", "").strip()))
        target_id = str(UUID(target_id))
    except (ValueError, AttributeError):
        return _error("invalid request", 400, request)
    if archive_id != configured_archive or action not in {"reset_password", "delete_user"}:
        return _error("invalid request", 400, request)
    if action == "reset_password" and not 8 <= len(password) <= 256:
        return _error("password must be 8 to 256 characters", 400, request)
    code, caller_body, _ = _http_call(_AUTH_ORIGIN, "/user", bearer=bearer)
    caller_id = str(caller_body.get("id") or "") if code == 200 and isinstance(caller_body, dict) else ""
    if not caller_id:
        return _error("invalid session", 401, request)
    member_code, members = _membership_rows(archive_id, user_id=caller_id, role="admin", status="active")
    if member_code != 200 or not members:
        return _error("admin access required", 403, request)
    target_code, target_rows = _membership_rows(archive_id, user_id=target_id)
    if target_code != 200 or not target_rows:
        return _error("user not found", 404, request)
    if action == "reset_password":
        status_code, _, _ = _auth_admin("PUT", "/admin/users/" + target_id, {"password": password})
        if status_code not in {200, 204}:
            return _error("password reset failed", 500, request)
        return Response(content=json.dumps({"success": True, "action": action}), media_type="application/json",
                        headers={"Cache-Control": "no-store", **_cors_headers(request)})
    if caller_id == target_id:
        return _error("you cannot delete your own admin account", 409, request)
    target = target_rows[0]
    if target.get("role") == "admin" and target.get("status") == "active":
        _, active_admins = _membership_rows(archive_id, role="admin", status="active")
        if len(active_admins) <= 1:
            return _error("cannot delete the last active admin", 409, request)
    status_code, _, _ = _auth_admin("DELETE", "/admin/users/" + target_id)
    if status_code not in {200, 204}:
        return _error("user deletion failed", 500, request)
    return Response(content=json.dumps({"success": True, "action": action}), media_type="application/json",
                    headers={"Cache-Control": "no-store", **_cors_headers(request)})


async def _local_complete_approved_account(request: Request) -> Response:
    if request.method != "POST":
        return _error("method not allowed", 405, request)
    try:
        body = await request.json()
    except Exception:
        return _error("invalid request", 400, request)
    email = str(body.get("email") or "").strip().lower()
    password = str(body.get("password") or "")
    token = str(body.get("approval_token") or "").strip()
    if not email or "@" not in email or len(email) > 320 or not 8 <= len(password) <= 256:
        return _error("invalid request", 400, request)
    try:
        token = str(UUID(token))
    except ValueError:
        return _error("invalid or expired approval", 403, request)
    params = parse.urlencode({"select": "id,archive_id,email,status,approved_role,approved_at", "email": f"eq.{email}",
                              "approval_token": f"eq.{token}", "status": "eq.approved", "limit": "1"})
    code, requests, _ = _service_rest("GET", "/account_access_requests?" + params)
    if code != 200 or not isinstance(requests, list) or not requests:
        return _error("invalid or expired approval", 403, request)
    access_request = requests[0]
    role = str(access_request.get("approved_role") or "")
    if role not in {"viewer", "editor", "admin"}:
        return _error("invalid or expired approval", 403, request)
    try:
        approved_at = datetime.fromisoformat(str(access_request.get("approved_at") or "").replace("Z", "+00:00"))
        if approved_at.tzinfo is None:
            approved_at = approved_at.replace(tzinfo=timezone.utc)
    except ValueError:
        return _error("invalid or expired approval", 403, request)
    if (datetime.now(timezone.utc) - approved_at).total_seconds() > 7 * 24 * 60 * 60:
        return _error("approval expired", 403, request)
    created_code, created, _ = _auth_admin("POST", "/admin/users", {"email": email, "password": password, "email_confirm": True})
    user_id = str(created.get("id") or (created.get("user") or {}).get("id") or "") if isinstance(created, dict) else ""
    newly_created = bool(user_id and created_code in {200, 201})
    if not user_id:
        list_code, listed, _ = _auth_admin("GET", "/admin/users?page=1&per_page=1000")
        users = listed.get("users", []) if isinstance(listed, dict) else listed if isinstance(listed, list) else []
        existing = next((u for u in users if isinstance(u, dict) and str(u.get("email") or "").lower() == email), None) if list_code == 200 else None
        if not existing:
            return _error("account activation failed", 500, request)
        user_id = str(existing.get("id") or "")
        update_code, _, _ = _auth_admin("PUT", "/admin/users/" + user_id, {"password": password, "email_confirm": True})
        if update_code not in {200, 204}:
            return _error("account activation failed", 500, request)
    now = datetime.now(timezone.utc).isoformat()
    member_payload = {"archive_id": str(access_request.get("archive_id")), "user_id": user_id,
                      "role": role, "status": "active", "updated_at": now}
    member_code, member_result, _ = _service_rest("POST", "/archive_members?on_conflict=archive_id%2Cuser_id",
                                                  member_payload, prefer="resolution=merge-duplicates,return=representation")
    if member_code not in {200, 201}:
        if newly_created:
            _auth_admin("DELETE", "/admin/users/" + user_id)
        return _error("account activation failed", 500, request)
    request_id = str(access_request.get("id") or "")
    update_params = parse.urlencode({"id": f"eq.{request_id}", "status": "eq.approved"})
    update_payload = {"status": "completed", "completed_at": now, "approval_token": None, "updated_at": now}
    complete_code, complete_result, _ = _service_rest("PATCH", "/account_access_requests?" + update_params,
                                                      update_payload, prefer="return=representation")
    if complete_code not in {200, 204} or not isinstance(complete_result, list) or not complete_result:
        return _error("account activation failed", 500, request)
    return Response(content='{"activated":true}', media_type="application/json",
                    headers={"Cache-Control": "no-store", **_cors_headers(request)})


def register_local_supabase_routes(app: FastAPI) -> None:
    """Register the compatibility surface only on the private Oracle API process."""
    enabled = os.environ.get("DLR_LOCAL_SUPABASE_PROXY_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        return

    methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]

    @app.api_route("/auth/v1/{path:path}", methods=methods, include_in_schema=False)
    async def local_auth_proxy(request: Request, path: str) -> Response:
        return await _forward(request, _AUTH_ORIGIN, path)

    @app.api_route("/rest/v1/{path:path}", methods=methods, include_in_schema=False)
    async def local_rest_proxy(request: Request, path: str) -> Response:
        return await _forward(request, _REST_ORIGIN, path)

    @app.api_route("/functions/v1/dlr-admin-user-account", methods=["POST", "OPTIONS"], include_in_schema=False)
    async def local_admin_user_account(request: Request) -> Response:
        if request.method == "OPTIONS":
            return Response(status_code=204, headers={**_cors_headers(request), "Cache-Control": "no-store"})
        request._body = await request.body()
        return await run_in_threadpool(_local_admin_user_account, request)

    @app.api_route("/functions/v1/dlr-complete-approved-account", methods=["POST", "OPTIONS"], include_in_schema=False)
    async def local_complete_approved_account(request: Request) -> Response:
        if request.method == "OPTIONS":
            return Response(status_code=204, headers={**_cors_headers(request), "Cache-Control": "no-store"})
        return await _local_complete_approved_account(request)
