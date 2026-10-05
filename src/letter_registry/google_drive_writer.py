"""Private Google Drive uploader for immutable archive originals.

OAuth credentials and folder references are runtime-only. The returned Drive
object ID remains server-side and is stored only in the private database.
"""

from __future__ import annotations

import json
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib import error, request

from .google_drive_auth import DriveAccessTokenProvider, StaticAccessTokenProvider, drive_token_provider_from_environment


class GoogleDriveWriteError(RuntimeError):
    pass


HttpExecutor = Callable[[request.Request], tuple[int, str]]


def _default_http_executor(req: request.Request) -> tuple[int, str]:
    try:
        with request.urlopen(req, timeout=90) as response:  # noqa: S310
            return response.status, response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GoogleDriveWriteError(
            f"Google Drive upload failed with HTTP {exc.code}: {body}"
        ) from exc
    except error.URLError as exc:
        raise GoogleDriveWriteError(
            f"Google Drive upload failed: {exc.reason}"
        ) from exc


@dataclass(slots=True)
class GoogleDrivePrivateWriter:
    access_token: str | None = None
    token_provider: DriveAccessTokenProvider | None = None
    http_executor: HttpExecutor = _default_http_executor

    @classmethod
    def from_environment(cls) -> "GoogleDrivePrivateWriter":
        return cls(token_provider=drive_token_provider_from_environment())

    def _token(self) -> str:
        if self.token_provider is not None:
            return self.token_provider.get_access_token()
        if self.access_token is not None:
            return StaticAccessTokenProvider(self.access_token).get_access_token()
        raise ValueError("Google Drive token provider is not configured")

    def replace_file(
        self,
        *,
        object_reference: str,
        path: Path,
    ) -> str:
        """Replace the bytes of an existing private Drive file in place."""
        if not path.is_file():
            raise ValueError("replacement path must be an existing file")
        object_id = object_reference.strip()
        if not object_id or "/" in object_id or "\\" in object_id:
            raise ValueError("invalid Google Drive object reference")

        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        req = request.Request(
            (
                f"https://www.googleapis.com/upload/drive/v3/files/{object_id}"
                "?uploadType=media&fields=id"
            ),
            data=path.read_bytes(),
            headers={
                "Authorization": f"Bearer {self._token()}",
                "Content-Type": content_type,
            },
            method="PATCH",
        )
        status, raw = self.http_executor(req)
        if status < 200 or status >= 300:
            raise GoogleDriveWriteError(
                f"unexpected Google Drive replace HTTP status: {status}"
            )
        try:
            returned_id = str(json.loads(raw)["id"]).strip()
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise GoogleDriveWriteError(
                "Google Drive returned an invalid replace response"
            ) from exc
        if returned_id != object_id:
            raise GoogleDriveWriteError("Google Drive replace returned an unexpected object ID")
        return returned_id

    def upload_file(
        self,
        *,
        folder_reference: str,
        filename: str,
        path: Path,
    ) -> str:
        if not path.is_file():
            raise ValueError("upload path must be an existing file")
        folder_id = folder_reference.strip()
        if not folder_id or "/" in folder_id or "\\" in folder_id:
            raise ValueError("invalid Google Drive folder reference")

        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        boundary = "dlr-upload-boundary"
        metadata = json.dumps(
            {
                "name": filename,
                "parents": [folder_id],
            },
            ensure_ascii=False,
        ).encode("utf-8")
        file_bytes = path.read_bytes()

        body = b"".join(
            [
                f"--{boundary}\r\n".encode(),
                b"Content-Type: application/json; charset=UTF-8\r\n\r\n",
                metadata,
                b"\r\n",
                f"--{boundary}\r\n".encode(),
                f"Content-Type: {content_type}\r\n\r\n".encode(),
                file_bytes,
                b"\r\n",
                f"--{boundary}--\r\n".encode(),
            ]
        )

        req = request.Request(
            (
                "https://www.googleapis.com/upload/drive/v3/files"
                "?uploadType=multipart&fields=id"
            ),
            data=body,
            headers={
                "Authorization": f"Bearer {self._token()}",
                "Content-Type": f"multipart/related; boundary={boundary}",
            },
            method="POST",
        )
        status, raw = self.http_executor(req)
        if status < 200 or status >= 300:
            raise GoogleDriveWriteError(
                f"unexpected Google Drive upload HTTP status: {status}"
            )

        try:
            object_id = str(json.loads(raw)["id"]).strip()
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise GoogleDriveWriteError(
                "Google Drive returned an invalid upload response"
            ) from exc

        if not object_id:
            raise GoogleDriveWriteError("Google Drive returned an empty object ID")
        return object_id
