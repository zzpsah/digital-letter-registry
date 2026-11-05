"""Vercel edge-facing reverse proxy for the Oracle-hosted DLR application.

Oracle FastAPI is the sole owner of PostgreSQL connections. Vercel forwards
HTTP traffic to Oracle and never opens a database connection from a serverless runtime.
"""
from __future__ import annotations

import os
from urllib.parse import urljoin

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

UPSTREAM_ORIGIN = os.environ.get(
    "DLR_NATIVE_API_ORIGIN",
    "https://oracle-server.tail2b7fe2.ts.net/dlr",
).strip().rstrip("/")
PROXY_TOKEN = os.environ.get("DLR_VERCEL_PROXY_TOKEN", "").strip()
_HOP_BY_HOP = {
    b"connection", b"keep-alive", b"proxy-authenticate", b"proxy-authorization",
    b"te", b"trailer", b"transfer-encoding", b"upgrade", b"host",
}
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

@app.middleware("http")
async def hide_legacy_auth_and_rest_routes(request: Request, call_next):
    if request.url.path.startswith(("/rest/v1", "/auth/v1", "/functions/v1")):
        return Response(status_code=404)
    return await call_next(request)


async def _close_upstream(upstream: httpx.Response, client: httpx.AsyncClient) -> None:
    await upstream.aclose()
    await client.aclose()


async def _forward(request: Request, path: str) -> StreamingResponse:
    if not UPSTREAM_ORIGIN.startswith("https://"):
        raise RuntimeError("DLR_NATIVE_API_ORIGIN must use HTTPS")
    target = urljoin(UPSTREAM_ORIGIN + "/", path)
    if request.url.query:
        target += "?" + request.url.query
    headers = [(key, value) for key, value in request.headers.raw if key.lower() not in _HOP_BY_HOP]
    if PROXY_TOKEN:
        headers.append((b"x-dlr-vercel-proxy-token", PROXY_TOKEN.encode("utf-8")))
    client = httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=15.0), follow_redirects=False)
    try:
        outgoing = client.build_request(request.method, target, headers=headers, content=request.stream())
        upstream = await client.send(outgoing, stream=True)
    except httpx.RequestError as exc:
        await client.aclose()
        raise RuntimeError("Oracle DLR API is temporarily unavailable") from exc
    response = StreamingResponse(
        upstream.aiter_raw(), status_code=upstream.status_code,
        background=BackgroundTask(_close_upstream, upstream, client),
    )
    response.raw_headers = [
        (key.lower(), value) for key, value in upstream.headers.raw
        if key.lower() not in _HOP_BY_HOP
    ]
    return response


@app.api_route("/", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def proxy_root(request: Request) -> StreamingResponse:
    return await _forward(request, "")


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def proxy_path(request: Request, path: str) -> StreamingResponse:
    return await _forward(request, path)
