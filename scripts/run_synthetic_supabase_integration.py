"""Run a guarded live synthetic Supabase integration test.

This command never uploads to Drive and refuses to run against a file whose
name does not clearly indicate synthetic/test content.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from uuid import UUID

from letter_registry.ingestion import prepare_source_record
from letter_registry.supabase_repository import SupabaseLetterRepository
from letter_registry.supabase_runtime import SupabasePostgrestTransport


def _synthetic_only(path: Path) -> None:
    name = path.name.lower()
    if "synthetic" not in name and "test" not in name:
        raise ValueError("refusing live integration: file must be clearly synthetic/test data")


def _owner_id_from_environment() -> str:
    value = os.environ.get("SUPABASE_OWNER_ID", "").strip()
    if not value:
        raise ValueError("SUPABASE_OWNER_ID is required at runtime")
    return str(UUID(value))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="local synthetic test file")
    parser.add_argument(
        "--storage-reference",
        required=True,
        help="opaque private storage object reference for the same synthetic file",
    )
    args = parser.parse_args()

    path = Path(args.file)
    _synthetic_only(path)
    owner_id = _owner_id_from_environment()
    transport = SupabasePostgrestTransport.from_environment()
    repository = SupabaseLetterRepository(transport)

    record = prepare_source_record(
        path,
        storage_reference=args.storage_reference,
    )

    repository.save_source(record, owner_id=owner_id)
    repository.save_processing_state(record, owner_id=owner_id)

    owner_rows = transport.select(
        "letters",
        filters={"original_sha256": record.original_sha256},
        columns="id,owner_id,original_sha256,original_filename",
    )
    if len(owner_rows) != 1:
        raise RuntimeError(f"expected exactly one owner-visible source row, got {len(owner_rows)}")

    repository.save_source(record, owner_id=owner_id)
    duplicate_rows = transport.select(
        "letters",
        filters={"original_sha256": record.original_sha256},
        columns="id,original_sha256",
    )
    if len(duplicate_rows) != 1:
        raise RuntimeError("duplicate protection failed")

    processing_rows = transport.select(
        "letter_processing",
        filters={"letter_id": record.record_id},
        columns="letter_id,owner_id,filename_rule_version",
    )
    if len(processing_rows) != 1:
        raise RuntimeError("processing initialization failed")

    print("synthetic integration passed")
    print(f"record_id={record.record_id}")
    print(f"sha256={record.original_sha256}")
    print("letters_rows=1")
    print("processing_rows=1")
    print("duplicate_protection=passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
