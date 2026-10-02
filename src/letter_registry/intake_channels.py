"""Provider-neutral intake-channel adapters.

Channel integrations only normalize an incoming attachment into a temporary
local file plus provenance. The canonical IntakeService remains the only place
that archives, deduplicates, persists, and queues documents.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .intake import IntakeResult


_SAFE_NAME = re.compile(r"[^\w.\-()\[\]\u0900-\u097F ]+", re.UNICODE)


def safe_attachment_filename(value: str) -> str:
    name = Path(value.strip()).name
    name = _SAFE_NAME.sub("-", name).strip(" .-")
    if not name or name in {".", ".."}:
        raise ValueError("incoming attachment filename is invalid")
    return name[:220]


@dataclass(frozen=True, slots=True)
class IntakeProvenance:
    channel: str
    source_id: str
    sender_label: str | None = None
    conversation_label: str | None = None

    def __post_init__(self) -> None:
        if self.channel not in {
            "watched_folder",
            "email",
            "telegram",
            "whatsapp",
            "web_upload",
        }:
            raise ValueError("unsupported intake channel")
        if not self.source_id.strip():
            raise ValueError("source_id is required")


@dataclass(frozen=True, slots=True)
class IncomingAttachment:
    path: Path
    filename: str
    provenance: IntakeProvenance

    def __post_init__(self) -> None:
        if not self.path.is_file():
            raise ValueError("incoming attachment path must be an existing file")
        safe_attachment_filename(self.filename)


class CanonicalIntake(Protocol):
    def ingest(self, path: str | Path, *, owner_id: str) -> IntakeResult:
        ...


@dataclass(frozen=True, slots=True)
class ChannelIntakeResult:
    intake: IntakeResult
    provenance: IntakeProvenance


@dataclass(slots=True)
class IntakeChannelAdapter:
    intake: CanonicalIntake

    def submit(
        self,
        attachment: IncomingAttachment,
        *,
        owner_id: str,
    ) -> ChannelIntakeResult:
        expected = safe_attachment_filename(attachment.filename)
        if expected != attachment.path.name:
            raise ValueError(
                "staged attachment filename must match normalized incoming filename"
            )
        result = self.intake.ingest(
            attachment.path,
            owner_id=owner_id,
        )
        return ChannelIntakeResult(
            intake=result,
            provenance=attachment.provenance,
        )


def watched_folder_attachment(path: str | Path) -> IncomingAttachment:
    source = Path(path)
    return IncomingAttachment(
        path=source,
        filename=source.name,
        provenance=IntakeProvenance(
            channel="watched_folder",
            source_id=str(source.resolve()),
        ),
    )


def email_attachment(
    path: str | Path,
    *,
    message_id: str,
    sender: str | None = None,
) -> IncomingAttachment:
    source = Path(path)
    return IncomingAttachment(
        path=source,
        filename=source.name,
        provenance=IntakeProvenance(
            channel="email",
            source_id=message_id,
            sender_label=sender,
        ),
    )


def telegram_attachment(
    path: str | Path,
    *,
    file_id: str,
    chat_label: str | None = None,
) -> IncomingAttachment:
    source = Path(path)
    return IncomingAttachment(
        path=source,
        filename=source.name,
        provenance=IntakeProvenance(
            channel="telegram",
            source_id=file_id,
            conversation_label=chat_label,
        ),
    )


def whatsapp_attachment(
    path: str | Path,
    *,
    message_id: str,
    chat_label: str | None = None,
    sender: str | None = None,
) -> IncomingAttachment:
    source = Path(path)
    return IncomingAttachment(
        path=source,
        filename=source.name,
        provenance=IntakeProvenance(
            channel="whatsapp",
            source_id=message_id,
            sender_label=sender,
            conversation_label=chat_label,
        ),
    )
