"""Private Google Drive uploader for immutable archive originals.

OAuth credentials and folder references are runtime-only. The returned Drive
object ID remains server-side and is stored only in the private database.
"""

from __future__ import annotations

import json
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib import error, request


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
    access_token: str
    http_executor: HttpExecutor = _default_http_executor

    @classmethod
    def from_environment(cls) -> "GoogleDrivePrivateWriter":
        token = os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN", "").strip()
        if not token:
            raise ValueError("GOOGLE_DRIVE_ACCESS_TOKEN is required at runtime")
        return cls(access_token=token)

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
                "Authorization": f"Bearer {self.access_token}",
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
