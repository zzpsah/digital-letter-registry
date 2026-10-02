"""Private Google Drive media reader for archived originals.

The Drive object ID stays server-side. OAuth access tokens are runtime-only and
must never be committed or returned to the browser.
"""

from __future__ import annotations

import mimetypes
import os
from dataclasses import dataclass
from typing import Callable
from urllib import error, parse, request

from .original_access import OriginalFile


class GoogleDriveReadError(RuntimeError):
    pass


BinaryHttpExecutor = Callable[[request.Request], tuple[int, bytes, str | None]]


def _default_binary_http_executor(
    req: request.Request,
) -> tuple[int, bytes, str | None]:
    try:
        with request.urlopen(req, timeout=60) as response:  # noqa: S310
            return (
                response.status,
                response.read(),
                response.headers.get("Content-Type"),
            )
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GoogleDriveReadError(
            f"Google Drive request failed with HTTP {exc.code}: {body}"
        ) from exc
    except error.URLError as exc:
        raise GoogleDriveReadError(
            f"Google Drive request failed: {exc.reason}"
        ) from exc


@dataclass(slots=True)
class GoogleDrivePrivateTransport:
    access_token: str
    http_executor: BinaryHttpExecutor = _default_binary_http_executor

    @classmethod
    def from_environment(cls) -> "GoogleDrivePrivateTransport":
        token = os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN", "").strip()
        if not token:
            raise ValueError("GOOGLE_DRIVE_ACCESS_TOKEN is required at runtime")
        return cls(access_token=token)

    def download(
        self,
        *,
        provider: str,
        object_reference: str,
        filename: str,
    ) -> OriginalFile:
        if provider != "gdrive":
            raise ValueError(f"unsupported storage provider: {provider}")
        object_id = object_reference.strip()
        if not object_id or "/" in object_id or "\" in object_id:
            raise ValueError("invalid Google Drive object reference")

        encoded_id = parse.quote(object_id, safe="")
        url = (
            "https://www.googleapis.com/drive/v3/files/"
            f"{encoded_id}?alt=media&supportsAllDrives=true"
        )
        req = request.Request(
            url,
            headers={"Authorization": f"Bearer {self.access_token}"},
            method="GET",
        )
        status, content, response_type = self.http_executor(req)
        if status < 200 or status >= 300:
            raise GoogleDriveReadError(
                f"unexpected Google Drive HTTP status: {status}"
            )

        guessed_type, _ = mimetypes.guess_type(filename)
        content_type = (
            (response_type or "").split(";", 1)[0].strip()
            or guessed_type
            or "application/octet-stream"
        )
        return OriginalFile(
            filename=filename,
            content_type=content_type,
            content=content,
        )
