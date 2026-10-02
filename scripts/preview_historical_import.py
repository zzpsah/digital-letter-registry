"""Create a non-destructive historical import preview report.

No storage/database mutations are performed. Duplicate checks use the
authenticated archive database if Supabase runtime credentials are provided.
"""

from __future__ import annotations

import os

import argparse
import csv
import json
from pathlib import Path

from letter_registry.historical_import import preview_historical_import
from letter_registry.session import SupabaseUserSession
from letter_registry.supabase_repository import SupabaseLetterRepository
from letter_registry.supabase_runtime import (
    ArchiveScopedSupabaseTransport,
    SupabasePostgrestTransport,
)


def candidate_files(root: Path, *, recursive: bool) -> list[Path]:
    pattern = "**/*" if recursive else "*"
    return sorted(path for path in root.glob(pattern) if path.is_file())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--recursive", action="store_true")
    args = parser.parse_args()

    root = Path(args.folder)
    if not root.is_dir():
        raise SystemExit("folder must exist")

    transport = ArchiveScopedSupabaseTransport(
        transport=SupabasePostgrestTransport.from_environment(),
        archive_id=os.environ["DLR_ARCHIVE_ID"],
    )
    owner_id = SupabaseUserSession.from_environment(
        access_token=transport.access_token,
    ).user_id()
    repository = SupabaseLetterRepository(transport)

    preview = preview_historical_import(
        candidate_files(root, recursive=args.recursive),
        owner_id=owner_id,
        repository=repository,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    if output.suffix.lower() == ".json":
        payload = {
            "total_files": preview.total_files,
            "new_files": preview.new_files,
            "duplicate_files": preview.duplicate_files,
            "total_bytes": preview.total_bytes,
            "candidates": [
                {
                    "original_filename": item.original_filename,
                    "sha256": item.sha256,
                    "size_bytes": item.size_bytes,
                    "extension": item.extension,
                    "duplicate": item.duplicate,
                }
                for item in preview.candidates
            ],
        }
        output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    else:
        with output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                (
                    "original_filename",
                    "sha256",
                    "size_bytes",
                    "extension",
                    "duplicate",
                )
            )
            for item in preview.candidates:
                writer.writerow(
                    (
                        item.original_filename,
                        item.sha256,
                        item.size_bytes,
                        item.extension,
                        "yes" if item.duplicate else "no",
                    )
                )

    print(f"total_files={preview.total_files}")
    print(f"new_files={preview.new_files}")
    print(f"duplicate_files={preview.duplicate_files}")
    print(f"total_bytes={preview.total_bytes}")
    print(f"report={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
