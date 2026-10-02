"""Private Google Drive filename mutation transport.

This adapter is intentionally not invoked automatically. It is designed to be
used only behind the approval-locked rename executor.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable
from urllib import error, parse, request

from .google_drive_auth import DriveAccessTokenProvider, StaticAccessTokenProvider, drive_token_provider_from_environment


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
    access_token: str | None = None
    token_provider: DriveAccessTokenProvider | None = None
    http_executor: HttpExecutor = _default_http_executor

    @classmethod
    def from_environment(cls) -> "GoogleDrivePrivateRenamer":
        return cls(token_provider=drive_token_provider_from_environment())

    def _token(self) -> str:
        if self.token_provider is not None:
            return self.token_provider.get_access_token()
        if self.access_token is not None:
            return StaticAccessTokenProvider(self.access_token).get_access_token()
        raise ValueError("Google Drive token provider is not configured")

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
                "Authorization": f"Bearer {self._token()}",
                "Content-Type": "application/json",
            },
            method="PATCH",
        )
        status, _ = self.http_executor(req)
        if status < 200 or status >= 300:
            raise GoogleDriveRenameError(
                f"unexpected Google Drive rename HTTP status: {status}"
            )
