"""Supabase Management API helper for hosted Auth configuration.

This module never persists or prints the management token. It only manages the
small Auth surface required by the Digital Letter Registry passwordless flow.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib import error, parse, request


class SupabaseManagementError(RuntimeError):
    pass


HttpExecutor = Callable[[request.Request], tuple[int, str]]


def _default_http_executor(req: request.Request) -> tuple[int, str]:
    try:
        with request.urlopen(req, timeout=30) as response:  # noqa: S310
            return response.status, response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SupabaseManagementError(
            f"Supabase Management API failed with HTTP {exc.code}: {body}"
        ) from exc
    except error.URLError as exc:
        raise SupabaseManagementError(
            f"Supabase Management API failed: {exc.reason}"
        ) from exc


def _project_ref_from_url(base_url: str) -> str:
    host = parse.urlsplit(base_url).hostname or ""
    suffix = ".supabase.co"
    if not host.endswith(suffix):
        raise ValueError("SUPABASE_URL must be a hosted supabase.co project URL")
    ref = host[: -len(suffix)].strip()
    if not ref:
        raise ValueError("could not derive Supabase project ref")
    return ref


def _origin(url: str) -> str:
    parsed = parse.urlsplit(url)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise ValueError("AUTH_APP_ORIGIN/AUTH_REDIRECT_URL must be an absolute URL")
    if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1"}:
        raise ValueError("HTTP app origin is allowed only for local development")
    return f"{parsed.scheme}://{parsed.netloc}"


def _merge_allow_list(current: str, required_url: str) -> str:
    items = [item.strip() for item in current.split(",") if item.strip()]
    if required_url not in items:
        items.append(required_url)
    return ",".join(items)


@dataclass(slots=True)
class SupabaseAuthConfigManager:
    project_ref: str
    management_token: str
    site_url: str
    redirect_url: str
    template_html: str
    google_client_id: str | None = None
    google_client_secret: str | None = None
    subject: str = "Your sign-in link"
    http_executor: HttpExecutor = _default_http_executor

    @classmethod
    def from_environment(
        cls,
        *,
        template_path: Path = Path("supabase/templates/magic-link.html"),
    ) -> "SupabaseAuthConfigManager":
        token = os.environ.get("SUPABASE_MANAGEMENT_ACCESS_TOKEN", "").strip()
        base_url = os.environ.get("SUPABASE_URL", "").strip()
        redirect = os.environ.get("AUTH_REDIRECT_URL", "").strip()
        app_origin = os.environ.get("AUTH_APP_ORIGIN", "").strip()
        google_client_id = os.environ.get(
            "GOOGLE_SIGNIN_OAUTH_CLIENT_ID", ""
        ).strip()
        google_client_secret = os.environ.get(
            "GOOGLE_SIGNIN_OAUTH_CLIENT_SECRET", ""
        ).strip()
        if bool(google_client_id) != bool(google_client_secret):
            raise ValueError(
                "Google Sign-In OAuth client id and secret must be supplied together"
            )
        if not token:
            raise ValueError("SUPABASE_MANAGEMENT_ACCESS_TOKEN is required")
        if not base_url:
            raise ValueError("SUPABASE_URL is required")
        if not redirect:
            raise ValueError("AUTH_REDIRECT_URL is required")
        if not template_path.is_file():
            raise ValueError("magic-link template file is missing")
        return cls(
            project_ref=_project_ref_from_url(base_url),
            management_token=token,
            site_url=_origin(app_origin or redirect),
            redirect_url=redirect,
            template_html=template_path.read_text(encoding="utf-8"),
            google_client_id=google_client_id or None,
            google_client_secret=google_client_secret or None,
        )

    @property
    def endpoint(self) -> str:
        return f"https://api.supabase.com/v1/projects/{self.project_ref}/config/auth"

    def _request(self, method: str, payload: dict[str, object] | None = None) -> dict[str, object]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {self.management_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method=method,
        )
        status, raw = self.http_executor(req)
        if status < 200 or status >= 300:
            raise SupabaseManagementError(f"unexpected Management API status: {status}")
        try:
            data = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError as exc:
            raise SupabaseManagementError("invalid Management API JSON response") from exc
        if not isinstance(data, dict):
            raise SupabaseManagementError("unexpected Management API response shape")
        return data

    def get_config(self) -> dict[str, object]:
        return self._request("GET")

    def desired_patch(
        self,
        current: dict[str, object],
        *,
        include_google_secret: bool = False,
    ) -> dict[str, object]:
        desired: dict[str, object] = {
            "site_url": self.site_url,
            "uri_allow_list": _merge_allow_list(
                str(current.get("uri_allow_list") or ""),
                self.redirect_url,
            ),
            "mailer_subjects_magic_link": self.subject,
            "mailer_templates_magic_link_content": self.template_html,
        }
        if self.google_client_id and self.google_client_secret:
            desired["external_google_enabled"] = True
            desired["external_google_client_id"] = self.google_client_id

        patch = {
            key: value
            for key, value in desired.items()
            if current.get(key) != value
        }
        if (
            include_google_secret
            and self.google_client_id
            and self.google_client_secret
        ):
            patch["external_google_secret"] = self.google_client_secret
        return patch

    def check(self) -> tuple[str, ...]:
        return tuple(
            self.desired_patch(
                self.get_config(),
                include_google_secret=False,
            ).keys()
        )

    def apply(self) -> tuple[str, ...]:
        current = self.get_config()
        patch = self.desired_patch(
            current,
            include_google_secret=True,
        )
        if patch:
            self._request("PATCH", patch)
        remaining = self.check()
        if remaining:
            raise SupabaseManagementError(
                "hosted Auth config still differs after apply: " + ", ".join(remaining)
            )
        return tuple(patch.keys())
