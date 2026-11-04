#!/usr/bin/env python3
"""Read-only archive-wide OCR, quality, queue and delivery audit."""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import datetime, timezone

from letter_registry.supabase_runtime import (
    ArchiveScopedSupabaseTransport,
    SupabasePostgrestTransport,
)


def _age_minutes(value: object) -> float | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - parsed).total_seconds() / 60)
    except (TypeError, ValueError):
        return None


def build_report(db: ArchiveScopedSupabaseTransport) -> dict[str, object]:
    letters = db.select(
        "letters",
        columns="id,title,category,issue_date,original_filename,created_at",
    )
    processing = db.select(
        "letter_processing",
        columns="letter_id,ocr_version,context_version,structured_context,reviewed_at,extracted_text",
    )
    jobs = db.select(
        "processing_jobs",
        columns="id,letter_id,status,reason,progress_stage,progress_percent,progress_detail,attempts,last_error,created_at,updated_at",
    )
    sources = db.select("letter_sources", columns="id,letter_id,metadata,created_at")

    letter_by_id = {str(row["id"]): row for row in letters}
    processing_by_id = {str(row["letter_id"]): row for row in processing}
    jobs_by_letter: dict[str, list[dict[str, object]]] = {}
    for job in jobs:
        jobs_by_letter.setdefault(str(job.get("letter_id") or ""), []).append(job)

    ocr_versions = Counter(str(row.get("ocr_version") or "unknown") for row in processing)
    job_statuses = Counter(str(row.get("status") or "unknown") for row in jobs)
    delivery_states = Counter(
        str(((row.get("metadata") or {}).get("delivery") or {}).get("pipeline_status") or "unset")
        for row in sources
    )
    quality_flags: Counter[str] = Counter()
    needs_review: list[dict[str, object]] = []
    missing_processing: list[dict[str, object]] = []
    for letter_id, letter in letter_by_id.items():
        proc = processing_by_id.get(letter_id)
        if proc is None:
            missing_processing.append({"letter_id": letter_id, "title": letter.get("title"), "filename": letter.get("original_filename")})
            continue
        context = proc.get("structured_context") or {}
        flags = [str(flag) for flag in (context.get("quality_flags") or [])]
        quality_flags.update(flags)
        confidence = context.get("confidence")
        try:
            low_confidence = confidence is not None and float(confidence) < 0.60
        except (TypeError, ValueError):
            low_confidence = True
        hard_review = bool(context.get("needs_reprocessing")) or low_confidence or bool(
            {"low_ocr_readability", "low_context_confidence", "no_clean_document_text", "missing_core_metadata", "missing_reference_and_date", "source_content_conflict", "missing_or_invalid_context_confidence"}.intersection(flags)
        )
        if hard_review and not proc.get("reviewed_at"):
            needs_review.append({
                "letter_id": letter_id,
                "title": letter.get("title"),
                "filename": letter.get("original_filename"),
                "category": letter.get("category"),
                "issue_date": letter.get("issue_date"),
                "ocr_version": proc.get("ocr_version"),
                "confidence": confidence,
                "needs_reprocessing": bool(context.get("needs_reprocessing")),
                "flags": flags,
                "extracted_characters": len(str(proc.get("extracted_text") or "")),
            })

    failed_jobs: list[dict[str, object]] = []
    active_jobs: list[dict[str, object]] = []
    stale_jobs: list[dict[str, object]] = []
    for job in jobs:
        status = str(job.get("status") or "")
        item = {
            "job_id": job.get("id"),
            "letter_id": job.get("letter_id"),
            "title": (letter_by_id.get(str(job.get("letter_id"))) or {}).get("title"),
            "filename": (letter_by_id.get(str(job.get("letter_id"))) or {}).get("original_filename"),
            "status": status,
            "reason": job.get("reason"),
            "stage": job.get("progress_stage"),
            "progress_percent": job.get("progress_percent"),
            "attempts": job.get("attempts"),
            "updated_at": job.get("updated_at"),
            "age_minutes": _age_minutes(job.get("updated_at")),
            "last_error": job.get("last_error"),
        }
        if status == "failed":
            failed_jobs.append(item)
        elif status in {"pending", "processing"}:
            active_jobs.append(item)
            if status == "processing" and (item["age_minutes"] or 0) >= 45:
                stale_jobs.append(item)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "configured DLR archive",
        "counts": {
            "letters": len(letters),
            "processing_rows": len(processing),
            "missing_processing_rows": len(missing_processing),
            "sources": len(sources),
            "jobs": len(jobs),
            "needs_human_quality_review": len(needs_review),
            "failed_jobs": len(failed_jobs),
            "pending_or_processing_jobs": len(active_jobs),
            "stale_processing_jobs_over_45m": len(stale_jobs),
        },
        "ocr_versions": dict(ocr_versions),
        "job_statuses": dict(job_statuses),
        "delivery_states": dict(delivery_states),
        "quality_flags": dict(quality_flags),
        "needs_human_quality_review": needs_review,
        "missing_processing_rows": missing_processing,
        "failed_jobs": failed_jobs,
        "pending_or_processing_jobs": active_jobs,
        "stale_processing_jobs": stale_jobs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    args = parser.parse_args()
    archive_id = os.environ.get("DLR_ARCHIVE_ID", "").strip()
    if not archive_id:
        parser.error("DLR_ARCHIVE_ID must be configured in the protected runtime")
    db = ArchiveScopedSupabaseTransport(
        transport=SupabasePostgrestTransport.from_worker_environment(),
        archive_id=archive_id,
    )
    report = build_report(db)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    print(f"# DLR document pipeline audit\n\nGenerated: {report['generated_at']}\n")
    for key, value in report["counts"].items():
        print(f"- **{key}:** {value}")
    for section in ("ocr_versions", "job_statuses", "delivery_states", "quality_flags"):
        print(f"\n## {section.replace('_', ' ').title()}\n")
        for key, value in report[section].items():
            print(f"- {key}: {value}")
    for section, title in (("needs_human_quality_review", "Needs human quality review"), ("failed_jobs", "Failed jobs"), ("pending_or_processing_jobs", "Pending / processing jobs"), ("stale_processing_jobs", "Stale processing jobs (45m+)"), ("missing_processing_rows", "Missing processing rows")):
        print(f"\n## {title}\n")
        for item in report[section]:
            print("- " + json.dumps(item, ensure_ascii=False, sort_keys=True))
        if not report[section]:
            print("- None")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
