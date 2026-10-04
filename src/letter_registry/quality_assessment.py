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




def normalize_confidence(value: object) -> float | None:
    """Normalize provider confidence without allowing malformed output to crash processing."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value)))

    text = str(value).strip().casefold()
    if not text:
        return None
    qualitative = {
        "high": 0.95,
        "very high": 0.98,
        "medium": 0.70,
        "moderate": 0.70,
        "low": 0.40,
        "very low": 0.20,
    }
    if text in qualitative:
        return qualitative[text]
    if text.endswith("%"):
        try:
            return max(0.0, min(1.0, float(text[:-1].strip()) / 100.0))
        except ValueError:
            return None
    try:
        numeric = float(text)
    except ValueError:
        return None
    if 1.0 < numeric <= 100.0:
        numeric /= 100.0
    return max(0.0, min(1.0, numeric))


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

    normalized_confidence = normalize_confidence(context_confidence)
    confidence = normalized_confidence if normalized_confidence is not None else 0.0
    if normalized_confidence is None:
        flags.append("missing_or_invalid_context_confidence")
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
