"""Private Google Drive filename mutation transport.

This adapter is intentionally not invoked automatically. It is designed to be
used only behind the approval-locked rename executor.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Callable
from urllib import error, parse, request


class GoogleDriveRenameError(RuntimeError):
    pass


HttpExecutor = Callable[[request.Request], tuple[int, str]]


def _default_http_executor(req: request.Request) -> tuple[int, str]:
    try:
        with request.urlopen(req, timeout=30) as response:  # noqa: S310
            return response.status, response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GoogleDriveRenameError(
            f"Google Drive rename failed with HTTP {exc.code}: {body}"
        ) from exc
    except error.URLError as exc:
        raise GoogleDriveRenameError(
            f"Google Drive rename failed: {exc.reason}"
        ) from exc


@dataclass(slots=True)
class GoogleDrivePrivateRenamer:
    access_token: str
    http_executor: HttpExecutor = _default_http_executor

    @classmethod
    def from_environment(cls) -> "GoogleDrivePrivateRenamer":
        token = os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN", "").strip()
        if not token:
            raise ValueError("GOOGLE_DRIVE_ACCESS_TOKEN is required at runtime")
        return cls(access_token=token)

    def rename(
        self,
        *,
        provider: str,
        object_reference: str,
        new_filename: str,
    ) -> None:
        if provider != "gdrive":
            raise ValueError(f"unsupported storage provider: {provider}")
        object_id = object_reference.strip()
        if not object_id or "/" in object_id or "\\" in object_id:
            raise ValueError("invalid Google Drive object reference")
        if not new_filename.strip() or "/" in new_filename or "\\" in new_filename:
            raise ValueError("invalid target filename")

        encoded_id = parse.quote(object_id, safe="")
        req = request.Request(
            (
                "https://www.googleapis.com/drive/v3/files/"
                f"{encoded_id}?fields=id,name&supportsAllDrives=true"
            ),
            data=json.dumps({"name": new_filename}, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
            method="PATCH",
        )
        status, _ = self.http_executor(req)
        if status < 200 or status >= 300:
            raise GoogleDriveRenameError(
                f"unexpected Google Drive rename HTTP status: {status}"
            )
