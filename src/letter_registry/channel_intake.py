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
class IntakeProvenance:
    channel: IntakeChannel
    filename: str
    received_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    external_message_id: str | None = None
    source_label: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if Path(self.filename).name != self.filename or not self.filename.strip():
            raise ValueError("filename must be a plain basename")
        if self.received_at.tzinfo is None:
            raise ValueError("received_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class InboundAttachment:
    provenance: IntakeProvenance
    content: bytes

    def __post_init__(self) -> None:
        if not self.content:
            raise ValueError("attachment content cannot be empty")

    @property
    def channel(self) -> IntakeChannel:
        return self.provenance.channel

    @property
    def filename(self) -> str:
        return self.provenance.filename


class ProvenanceRepository(Protocol):
    def save_source(
        self,
        *,
        owner_id: str,
        letter_id: str,
        provenance: IntakeProvenance,
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
        provenance: IntakeProvenance,
    ) -> None:
        UUID(owner_id)
        UUID(letter_id)
        if provenance.external_message_id:
            existing = self.transport.select(
                "letter_sources",
                filters={
                    "source_channel": provenance.channel.value,
                    "external_message_id": provenance.external_message_id,
                },
                columns="id",
            )
            if existing:
                return

        self.transport.insert(
            "letter_sources",
            {
                "owner_id": owner_id,
                "letter_id": letter_id,
                "source_channel": provenance.channel.value,
                "external_message_id": provenance.external_message_id,
                "source_label": provenance.source_label,
                "received_at": provenance.received_at.isoformat(),
                "metadata": dict(provenance.metadata),
            },
        )


@dataclass(slots=True)
class ChannelIntakeService:
    intake: IntakeService
    provenance: ProvenanceRepository

    @property
    def policy(self):
        return self.intake.policy

    def ingest_path(
        self,
        path: str | Path,
        *,
        owner_id: str,
        provenance: IntakeProvenance,
    ) -> IntakeResult:
        source = Path(path)
        if source.name != provenance.filename:
            raise ValueError("provenance filename must match the intake file")

        result = self.intake.ingest(source, owner_id=owner_id)
        self.provenance.save_source(
            owner_id=owner_id,
            letter_id=result.record.record_id,
            provenance=provenance,
        )
        return result

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
            return self.ingest_path(
                path,
                owner_id=owner_id,
                provenance=attachment.provenance,
            )
