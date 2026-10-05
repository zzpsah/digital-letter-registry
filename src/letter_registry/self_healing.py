from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib

from .jobs import ProcessingQueue


QUALITY_VERSION = "document-quality-v1"


def provider_tier(version: str) -> int:
    value = str(version or "").casefold()
    if "gemini" in value:
        return 3
    if "hermes" in value:
        return 2
    if "deterministic" in value:
        return 1
    return 0


@dataclass(frozen=True, slots=True)
class SelfHealingScanResult:
    scanned: int
    low_quality: int
    enqueued: int
    skipped_same_target: int


@dataclass(slots=True)
class SelfHealingReprocessor:
    transport: object
    queue: ProcessingQueue

    def scan(
        self,
        *,
        target_context_version: str,
        target_dictionary_version: str,
        target_quality_version: str = QUALITY_VERSION,
        limit: int = 100,
        max_enqueues: int = 5,
        now: datetime | None = None,
    ) -> SelfHealingScanResult:
        if limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")
        if max_enqueues < 1 or max_enqueues > 50:
            raise ValueError("max_enqueues must be between 1 and 50")
        target_context_version = str(target_context_version or "").strip()
        target_dictionary_version = str(target_dictionary_version or "").strip()
        if not target_context_version or not target_dictionary_version:
            raise ValueError("target context and dictionary versions are required")

        rows = self.transport.select(
            "letter_processing",
            columns=(
                "letter_id,owner_id,context_version,dictionary_version,"
                "structured_context"
            ),
        )
        current_time = now or datetime.now(timezone.utc)
        day_bucket = current_time.strftime("%Y%m%d")
        target_tier = provider_tier(target_context_version)

        scanned = 0
        low_quality = 0
        enqueued = 0
        skipped_same_target = 0

        for row in rows[:limit]:
            scanned += 1
            structured = row.get("structured_context")
            if not isinstance(structured, dict) or not bool(
                structured.get("needs_reprocessing")
            ):
                continue
            low_quality += 1

            stored_context = str(row.get("context_version") or "").strip()
            stored_dictionary = str(row.get("dictionary_version") or "").strip()
            stored_quality = str(structured.get("quality_version") or "").strip()
            stored_tier = provider_tier(stored_context)

            higher_provider_waiting = target_tier > stored_tier
            version_upgrade = (
                target_tier == stored_tier
                and target_context_version != stored_context
            )
            dictionary_upgrade = target_dictionary_version != stored_dictionary
            quality_upgrade = target_quality_version != stored_quality

            if not (
                higher_provider_waiting
                or version_upgrade
                or dictionary_upgrade
                or quality_upgrade
            ):
                skipped_same_target += 1
                continue

            if enqueued >= max_enqueues:
                continue

            target_signature = "|".join(
                (
                    target_context_version,
                    target_dictionary_version,
                    target_quality_version,
                )
            )
            digest = hashlib.sha256(target_signature.encode()).hexdigest()[:16]

            if higher_provider_waiting and not (
                version_upgrade or dictionary_upgrade or quality_upgrade
            ):
                reason = f"quality-recovery:{digest}:{day_bucket}"
            else:
                reason = f"quality-upgrade:{digest}"

            before = self.transport.select(
                "processing_jobs",
                filters={
                    "letter_id": str(row["letter_id"]),
                    "reason": reason,
                },
                columns="id",
            )
            self.queue.enqueue(
                letter_id=str(row["letter_id"]),
                owner_id=str(row["owner_id"]),
                reason=reason,
            )
            if not before:
                enqueued += 1

        return SelfHealingScanResult(
            scanned=scanned,
            low_quality=low_quality,
            enqueued=enqueued,
            skipped_same_target=skipped_same_target,
        )
