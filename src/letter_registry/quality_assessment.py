from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True, slots=True)
class DocumentQualityAssessment:
    score: float
    needs_reprocessing: bool
    flags: tuple[str, ...]
    version: str = "document-quality-v1"


def _readability_score(text: str) -> float:
    value = str(text or "").strip()
    if not value:
        return 0.0
    length = max(len(value), 1)
    alnum = sum(ch.isalnum() for ch in value) / length
    replacement = value.count("�") / length
    private_use = sum(unicodedata.category(ch) == "Co" for ch in value) / length
    odd = sum(ch in "|{}[]<>_=\\^~" for ch in value) / length
    token_count = len(re.findall(r"\w+", value, flags=re.UNICODE))
    length_factor = min(1.0, token_count / 80.0)
    score = (
        0.55 * min(1.0, alnum / 0.55)
        + 0.25 * length_factor
        + 0.20 * max(0.0, 1.0 - (replacement * 80 + private_use * 30 + odd * 8))
    )
    return max(0.0, min(1.0, score))


def assess_document_quality(
    *,
    extracted_text: str,
    context_confidence: float | None,
    title: str | None,
    authority: str | None,
    category: str | None,
    reference_number: str | None,
    issue_date: str | None,
    clean_document_text: str | None,
    threshold: float = 0.72,
) -> DocumentQualityAssessment:
    flags: list[str] = []
    readability = _readability_score(extracted_text)
    if readability < 0.55:
        flags.append("low_ocr_readability")

    confidence = float(context_confidence) if context_confidence is not None else 0.0
    confidence = max(0.0, min(1.0, confidence))
    if context_confidence is None:
        flags.append("missing_context_confidence")
    elif confidence < 0.75:
        flags.append("low_context_confidence")

    core_fields = (title, authority, category)
    core_completeness = sum(bool(str(x or "").strip()) for x in core_fields) / len(core_fields)
    if core_completeness < 1.0:
        flags.append("missing_core_metadata")

    identity_fields = (reference_number, issue_date)
    identity_completeness = sum(bool(str(x or "").strip()) for x in identity_fields) / len(identity_fields)
    if identity_completeness == 0:
        flags.append("missing_reference_and_date")

    clean_bonus = 1.0 if str(clean_document_text or "").strip() else 0.0
    if not clean_bonus:
        flags.append("no_clean_document_text")

    score = (
        0.35 * readability
        + 0.35 * confidence
        + 0.20 * core_completeness
        + 0.05 * identity_completeness
        + 0.05 * clean_bonus
    )
    score = round(max(0.0, min(1.0, score)), 4)

    return DocumentQualityAssessment(
        score=score,
        needs_reprocessing=score < threshold,
        flags=tuple(flags),
    )
