"""Ingest one already-authorized WhatsApp attachment into DLR.

Runtime-only identifiers/credentials are supplied through environment/arguments.
This script never connects to WhatsApp itself.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from letter_registry.channel_intake import (
    ChannelIntakeService,
    IntakeChannel,
    IntakeProvenance,
    SupabaseProvenanceRepository,
)
from letter_registry.google_drive_writer import GoogleDrivePrivateWriter
from letter_registry.fingerprints import sha256_file
from letter_registry.intake import DuplicateSourceError, IntakePolicy, IntakeService
from letter_registry.jobs import SupabaseProcessingQueue
from letter_registry.session import SupabaseUserSession
from letter_registry.storage import GoogleDriveOriginalStorage
from letter_registry.supabase_repository import SupabaseLetterRepository
from letter_registry.supabase_runtime import (
    ArchiveScopedSupabaseTransport,
    SupabasePostgrestTransport,
)


def _truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _limit() -> int:
    raw = os.environ.get("DLR_WHATSAPP_REAL_INTAKE_LIMIT", "").strip()
    if not raw:
        raise RuntimeError("DLR_WHATSAPP_REAL_INTAKE_LIMIT is required")
    value = int(raw)
    if value < 1 or value > 500:
        raise RuntimeError("DLR_WHATSAPP_REAL_INTAKE_LIMIT must be between 1 and 500")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True)
    parser.add_argument("--message-id", required=True)
    parser.add_argument("--source-label", default="WhatsApp")
    parser.add_argument("--reply-chat-id", default="")
    parser.add_argument("--query-text", default="")
    args = parser.parse_args()

    path = Path(args.path)
    if path.suffix.lower() not in {".pdf", ".jpg", ".jpeg", ".png"}:
        raise SystemExit("unsupported attachment type")
    if not _truthy("DLR_WHATSAPP_REAL_INTAKE_ENABLED"):
        raise SystemExit("WhatsApp real intake is disabled")

    raw = SupabasePostgrestTransport.from_worker_environment()
    owner_id = SupabaseUserSession.from_environment(
        access_token=raw.access_token
    ).user_id()
    transport = ArchiveScopedSupabaseTransport(
        transport=raw,
        archive_id=os.environ["DLR_ARCHIVE_ID"],
    )

    existing = transport.select(
        "letter_sources",
        filters={"source_channel": "whatsapp"},
        columns="id",
    )
    limit = _limit()
    if len(existing) >= limit:
        raise SystemExit(f"WhatsApp intake limit reached ({limit})")

    provenance = IntakeProvenance(
        channel=IntakeChannel.WHATSAPP,
        filename=path.name,
        external_message_id=args.message_id,
        source_label=args.source_label,
        metadata={
            "connector": "hermes-whatsapp",
            "reply_chat_id": args.reply_chat_id.strip() or None,
            "query_text": args.query_text.strip() or None,
        },
    )
    source_repo = SupabaseProvenanceRepository(transport)
    existing_message = transport.select(
        "letter_sources",
        filters={
            "source_channel": "whatsapp",
            "external_message_id": args.message_id,
        },
        columns="id,letter_id",
    )
    if existing_message:
        print("status=duplicate-message")
        return 0

    letter_repo = SupabaseLetterRepository(transport)
    service = ChannelIntakeService(
        intake=IntakeService(
            storage=GoogleDriveOriginalStorage(
                transport=GoogleDrivePrivateWriter.from_environment(),
                originals_folder_reference=os.environ[
                    "DRIVE_ORIGINALS_FOLDER_REFERENCE"
                ],
            ),
            repository=letter_repo,
            queue=SupabaseProcessingQueue(transport),
            policy=IntakePolicy(synthetic_only=False),
        ),
        provenance=source_repo,
    )

    try:
        result = service.ingest_path(
            path,
            owner_id=owner_id,
            provenance=provenance,
        )
    except DuplicateSourceError:
        rows = transport.select(
            "letters",
            filters={"original_sha256": sha256_file(path)},
            columns="id",
        )
        if not rows:
            raise
        source_repo.save_source(
            owner_id=owner_id,
            letter_id=str(rows[0]["id"]),
            provenance=provenance,
        )
        print("status=duplicate-provenance-linked")
        return 0

    print("status=queued")
    print(f"letter_id={result.record.record_id}")
    print(f"job_id={result.job.job_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
