"""Provider-neutral intake-channel normalization and provenance."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Mapping, Protocol
from uuid import UUID

from .intake import IntakeResult, IntakeService


class IntakeChannel(StrEnum):
    WEB = "web"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    WATCHED_FOLDER = "watched_folder"
    HISTORICAL_IMPORT = "historical_import"


@dataclass(frozen=True, slots=True)
class InboundAttachment:
    channel: IntakeChannel
    filename: str
    content: bytes
    received_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    external_message_id: str | None = None
    source_label: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if Path(self.filename).name != self.filename or not self.filename.strip():
            raise ValueError("filename must be a plain basename")
        if not self.content:
            raise ValueError("attachment content cannot be empty")
        if self.received_at.tzinfo is None:
            raise ValueError("received_at must be timezone-aware")


class ProvenanceRepository(Protocol):
    def save_source(
        self,
        *,
        owner_id: str,
        letter_id: str,
        attachment: InboundAttachment,
    ) -> None:
        ...


@dataclass(slots=True)
class SupabaseProvenanceRepository:
    transport: object

    def save_source(
        self,
        *,
        owner_id: str,
        letter_id: str,
        attachment: InboundAttachment,
    ) -> None:
        UUID(owner_id)
        UUID(letter_id)
        self.transport.insert(
            "letter_sources",
            {
                "owner_id": owner_id,
                "letter_id": letter_id,
                "source_channel": attachment.channel.value,
                "external_message_id": attachment.external_message_id,
                "source_label": attachment.source_label,
                "received_at": attachment.received_at.isoformat(),
                "metadata": dict(attachment.metadata),
            },
            on_conflict=(
                "owner_id,source_channel,external_message_id"
                if attachment.external_message_id
                else None
            ),
        )


@dataclass(slots=True)
class ChannelIntakeService:
    intake: IntakeService
    provenance: ProvenanceRepository

    def ingest(
        self,
        attachment: InboundAttachment,
        *,
        owner_id: str,
    ) -> IntakeResult:
        """Normalize any channel into the same immutable archive intake path."""

        with TemporaryDirectory() as directory:
            path = Path(directory) / attachment.filename
            path.write_bytes(attachment.content)
            result = self.intake.ingest(path, owner_id=owner_id)

        self.provenance.save_source(
            owner_id=owner_id,
            letter_id=result.record.record_id,
            attachment=attachment,
        )
        return result
