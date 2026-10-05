#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from letter_registry.supabase_runtime import (
    ArchiveScopedSupabaseTransport,
    SupabasePostgrestTransport,
)

DEFAULT_OUT = Path("/home/prashant/.hermes/state/dlr-benchmark/latest.json")


@dataclass
class RowScore:
    letter_id: str
    filename: str
    score: int
    grade: str
    checks: dict[str, bool]
    notes: list[str]


def _bool(value: object) -> bool:
    return bool(str(value or "").strip())


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    return "D"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--output", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    if args.limit < 1 or args.limit > 100:
        raise SystemExit("--limit must be 1..100")

    transport = ArchiveScopedSupabaseTransport(
        transport=SupabasePostgrestTransport.from_worker_environment(),
        archive_id=os.environ["DLR_ARCHIVE_ID"],
    )
    letters = transport.select(
        "letters",
        columns=(
            "id,received_at,original_filename,smart_filename,title,authority,"
            "reference_number,issue_date,category,storage_provider,storage_object_id"
        ),
    )
    letters = [
        row for row in letters
        if "synthetic" not in str(row.get("original_filename") or "").casefold()
    ]
    letters.sort(key=lambda row: str(row.get("received_at") or ""), reverse=True)
    sample = letters[: args.limit]

    scored: list[RowScore] = []
    for letter in sample:
        letter_id = str(letter["id"])
        processing_rows = transport.select(
            "letter_processing",
            filters={"letter_id": letter_id},
            columns="extracted_text,structured_context,context_version,concepts",
        )
        source_rows = transport.select(
            "letter_sources",
            filters={"letter_id": letter_id},
            columns="source_channel,metadata",
        )
        processing = processing_rows[0] if processing_rows else {}
        structured = (
            processing.get("structured_context")
            if isinstance(processing.get("structured_context"), dict)
            else {}
        )
        extracted = str(processing.get("extracted_text") or "")
        sources = [s for s in source_rows if str(s.get("source_channel") or "") == "whatsapp"]
        delivery_meta = {}
        for source in sources:
            metadata = source.get("metadata") if isinstance(source.get("metadata"), dict) else {}
            delivery = metadata.get("delivery") if isinstance(metadata.get("delivery"), dict) else {}
            if delivery:
                delivery_meta = delivery
                break

        checks = {
            "processed": bool(processing_rows),
            "extracted_text": len(extracted.strip()) >= 80,
            "title": _bool(letter.get("title")),
            "authority": _bool(letter.get("authority")),
            "category": _bool(letter.get("category")),
            "identity": _bool(letter.get("reference_number")) or _bool(letter.get("issue_date")),
            "smart_filename": _bool(letter.get("smart_filename")),
            "quality_scored": structured.get("quality_score") is not None,
            "quality_ok": not bool(structured.get("needs_reprocessing")),
            "context_engine": _bool(processing.get("context_version")),
            "search_terms": bool(processing.get("concepts")) or len(extracted.strip()) >= 200,
            "drive_object": _bool(letter.get("storage_object_id")),
            "drive_renamed": (
                not _bool(letter.get("smart_filename"))
                or str(delivery_meta.get("drive_renamed_to") or "") == str(letter.get("smart_filename") or "")
            ),
            "email_sent": (
                not sources
                or str(delivery_meta.get("email_package_status") or "") == "sent"
            ),
        }

        weights = {
            "processed": 10,
            "extracted_text": 10,
            "title": 8,
            "authority": 7,
            "category": 7,
            "identity": 6,
            "smart_filename": 8,
            "quality_scored": 8,
            "quality_ok": 8,
            "context_engine": 6,
            "search_terms": 8,
            "drive_object": 4,
            "drive_renamed": 5,
            "email_sent": 5,
        }
        score = sum(weights[k] for k, ok in checks.items() if ok)
        notes: list[str] = []
        if not checks["quality_scored"]:
            notes.append("legacy processing has no quality score")
        if structured.get("needs_reprocessing"):
            notes.append("automatic reprocessing recommended")
        if not checks["identity"]:
            notes.append("reference/date not detected")
        if not checks["authority"]:
            notes.append("authority not detected")
        if not checks["smart_filename"]:
            notes.append("smart filename missing")
        if not checks["email_sent"]:
            notes.append("email delivery not reconciled")
        notes.append("manual factual truth check required for title/authority/date/ref correctness")

        scored.append(
            RowScore(
                letter_id=letter_id,
                filename=str(letter.get("smart_filename") or letter.get("original_filename") or ""),
                score=score,
                grade=_grade(score),
                checks=checks,
                notes=notes,
            )
        )

    avg = round(sum(r.score for r in scored) / len(scored), 1) if scored else 0.0
    payload = {
        "benchmark_version": "dlr-real-letter-benchmark-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "requested_limit": args.limit,
        "available_real_documents": len(letters),
        "sample_size": len(scored),
        "average_score": avg,
        "grade": _grade(round(avg)) if scored else "N/A",
        "manual_truth_check_required": True,
        "rows": [asdict(r) for r in scored],
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    out.chmod(0o600)

    print(f"sample_size={len(scored)}")
    print(f"available_real_documents={len(letters)}")
    print(f"average_score={avg}")
    print(f"grade={payload['grade']}")
    for row in scored:
        failed = ",".join(k for k, ok in row.checks.items() if not ok) or "-"
        print(f"{row.score:3d} {row.grade} {row.filename} | failed={failed}")
    print(f"report={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
