"""Private Google Drive folder catalog for historical archive discovery.

Only the backend sees Drive object IDs. Listing is read-only and does not import,
rename, move, or modify files.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from urllib import error, parse, request

from .google_drive_auth import (
    DriveAccessTokenProvider,
    StaticAccessTokenProvider,
    drive_token_provider_from_environment,
)


class GoogleDriveCatalogError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class HistoricalDriveItem:
    object_reference: str
    filename: str
    mime_type: str | None
    size_bytes: int | None
    modified_at: datetime | None


HttpExecutor = Callable[[request.Request], tuple[int, str]]


def _default_http_executor(req: request.Request) -> tuple[int, str]:
    try:
        with request.urlopen(req, timeout=60) as response:  # noqa: S310
            return response.status, response.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GoogleDriveCatalogError(
            f"Google Drive catalog failed with HTTP {exc.code}: {body}"
        ) from exc
    except error.URLError as exc:
        raise GoogleDriveCatalogError(
            f"Google Drive catalog failed: {exc.reason}"
        ) from exc


@dataclass(slots=True)
class GoogleDrivePrivateCatalog:
    access_token: str | None = None
    token_provider: DriveAccessTokenProvider | None = None
    http_executor: HttpExecutor = _default_http_executor

    @classmethod
    def from_environment(cls) -> "GoogleDrivePrivateCatalog":
        return cls(token_provider=drive_token_provider_from_environment())

    def _token(self) -> str:
        if self.token_provider is not None:
            return self.token_provider.get_access_token()
        if self.access_token is not None:
            return StaticAccessTokenProvider(
                self.access_token
            ).get_access_token()
        raise ValueError("Google Drive token provider is not configured")

    def list_folder(
        self,
        folder_reference: str,
        *,
        max_items: int = 1000,
    ) -> list[HistoricalDriveItem]:
        folder_id = folder_reference.strip()
        if not folder_id or "/" in folder_id or "\\" in folder_id:
            raise ValueError("invalid Google Drive folder reference")
        if max_items < 1 or max_items > 10000:
            raise ValueError("max_items must be between 1 and 10000")

        items: list[HistoricalDriveItem] = []
        page_token: str | None = None

        while len(items) < max_items:
            query = {
                "q": f"'{folder_id}' in parents and trashed = false",
                "pageSize": str(min(1000, max_items - len(items))),
                "fields": (
                    "nextPageToken,"
                    "files(id,name,mimeType,size,modifiedTime)"
                ),
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true",
            }
            if page_token:
                query["pageToken"] = page_token

            req = request.Request(
                "https://www.googleapis.com/drive/v3/files?"
                + parse.urlencode(query),
                headers={
                    "Authorization": f"Bearer {self._token()}",
                    "Accept": "application/json",
                },
                method="GET",
            )
            status, raw = self.http_executor(req)
            if status < 200 or status >= 300:
                raise GoogleDriveCatalogError(
                    f"unexpected Google Drive catalog HTTP status: {status}"
                )

            try:
                data = json.loads(raw)
                files = data.get("files", [])
            except json.JSONDecodeError as exc:
                raise GoogleDriveCatalogError(
                    "Google Drive returned invalid catalog JSON"
                ) from exc

            for item in files:
                if not isinstance(item, dict):
                    continue
                object_id = str(item.get("id") or "").strip()
                filename = str(item.get("name") or "").strip()
                if not object_id or not filename:
                    continue

                size_raw = item.get("size")
                size_bytes = (
                    int(size_raw)
                    if size_raw is not None and str(size_raw).isdigit()
                    else None
                )
                modified_raw = item.get("modifiedTime")
                modified_at = None
                if modified_raw:
                    try:
                        modified_at = datetime.fromisoformat(
                            str(modified_raw).replace("Z", "+00:00")
                        )
                    except ValueError:
                        modified_at = None

                items.append(
                    HistoricalDriveItem(
                        object_reference=object_id,
                        filename=filename,
                        mime_type=(
                            str(item["mimeType"])
                            if item.get("mimeType") is not None
                            else None
                        ),
                        size_bytes=size_bytes,
                        modified_at=modified_at,
                    )
                )
                if len(items) >= max_items:
                    break

            page_token = str(data.get("nextPageToken") or "").strip() or None
            if not page_token:
                break

        return items
