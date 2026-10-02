"""Channel-specific normalization helpers.

These adapters do not connect to Telegram, WhatsApp, Gmail, or the filesystem
watcher themselves. They translate already-authorized provider payloads into
the shared InboundAttachment contract.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from .channel_intake import InboundAttachment, IntakeChannel, IntakeProvenance


def telegram_attachment(
    *,
    filename: str,
    content: bytes,
    message_id: str,
    chat_label: str | None = None,
    received_at: datetime | None = None,
    metadata: Mapping[str, object] | None = None,
) -> InboundAttachment:
    return InboundAttachment(
        provenance=IntakeProvenance(
            channel=IntakeChannel.TELEGRAM,
            filename=Path(filename).name,
            received_at=received_at or datetime.now(timezone.utc),
            external_message_id=message_id,
            source_label=chat_label,
            metadata=metadata or {},
        ),
        content=content,
    )


def whatsapp_attachment(
    *,
    filename: str,
    content: bytes,
    message_id: str,
    chat_label: str | None = None,
    received_at: datetime | None = None,
    metadata: Mapping[str, object] | None = None,
) -> InboundAttachment:
    return InboundAttachment(
        provenance=IntakeProvenance(
            channel=IntakeChannel.WHATSAPP,
            filename=Path(filename).name,
            received_at=received_at or datetime.now(timezone.utc),
            external_message_id=message_id,
            source_label=chat_label,
            metadata=metadata or {},
        ),
        content=content,
    )


def email_attachment(
    *,
    filename: str,
    content: bytes,
    message_id: str,
    sender_label: str | None = None,
    received_at: datetime | None = None,
    metadata: Mapping[str, object] | None = None,
) -> InboundAttachment:
    return InboundAttachment(
        provenance=IntakeProvenance(
            channel=IntakeChannel.EMAIL,
            filename=Path(filename).name,
            received_at=received_at or datetime.now(timezone.utc),
            external_message_id=message_id,
            source_label=sender_label,
            metadata=metadata or {},
        ),
        content=content,
    )


def watched_file_attachment(
    path: str | Path,
    *,
    source_label: str | None = None,
    received_at: datetime | None = None,
    metadata: Mapping[str, object] | None = None,
) -> InboundAttachment:
    source = Path(path)
    if not source.is_file():
        raise ValueError("watched file must exist")
    return InboundAttachment(
        provenance=IntakeProvenance(
            channel=IntakeChannel.WATCHED_FOLDER,
            filename=source.name,
            received_at=received_at or datetime.now(timezone.utc),
            source_label=source_label,
            metadata=metadata or {},
        ),
        content=source.read_bytes(),
    )
