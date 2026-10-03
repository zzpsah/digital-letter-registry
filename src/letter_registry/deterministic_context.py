"""Deterministic structured context fallback when no AI provider is configured.

The fallback is intentionally conservative. It derives only broad labels from
the checked-in vocabulary and never invents dates, reference numbers, deadlines,
or specific actions.
"""

from __future__ import annotations

from dataclasses import dataclass

from .context_hints import ContextHints
from .extraction import normalize_extracted_text
from .structured_analysis import StructuredDocumentContext


def _authority(text: str) -> str | None:
    folded = f" {text.casefold()} "
    if "बिहार विद्यालय परीक्षा समिति" in folded or " bseb " in folded:
        return "BSEB"
    if "udise" in folded or "यूडाइस" in folded:
        return "UDISE+"
    if (
        "eshikshakosh" in folded
        or "e-shikshakosh" in folded
        or "ईशिक्षाकोष" in folded
    ):
        return "eShikshaKosh"
    if "शिक्षा विभाग" in folded or "education department" in folded:
        return "Education Department"
    return None


def _category(concepts: tuple[str, ...]) -> str | None:
    values = set(concepts)
    if values & {"exam_form", "matric", "intermediate"}:
        return "exam"
    if "registration" in values:
        return "registration"
    if values & {"udise", "pen", "apaar"}:
        return "student-data"
    for value in ("scholarship", "admission", "attendance", "fee", "training"):
        if value in values:
            return value
    if values & {"correction", "verification"}:
        return "data-quality"
    return None


def _title(concepts: tuple[str, ...]) -> str | None:
    values = set(concepts)
    if "deadline_extension" in values and "exam_form" in values:
        return "Exam Form Deadline Extension"
    if "deadline_extension" in values and "registration" in values:
        return "Registration Deadline Extension"
    if "exam_form" in values:
        return "Exam Form Notice"
    if "registration" in values:
        return "Registration Notice"
    if "udise" in values:
        return "UDISE Notice"
    if "eshikshakosh" in values:
        return "eShikshaKosh Notice"
    if "scholarship" in values:
        return "Scholarship Notice"
    if "admission" in values:
        return "Admission Notice"
    return None


@dataclass(frozen=True, slots=True)
class DeterministicDocumentContextProvider:
    """Vocabulary-only fallback suitable for OCR/full-text indexing."""

    version: str = "deterministic:hints-v1"
    summary_characters: int = 280

    def analyze(
        self,
        *,
        extracted_text: str,
        hints: ContextHints,
    ) -> StructuredDocumentContext:
        normalized = normalize_extracted_text(extracted_text)
        summary = normalized[: self.summary_characters].strip() or None
        concepts = tuple(dict.fromkeys(hints.concepts))
        return StructuredDocumentContext(
            title=_title(concepts),
            authority=_authority(normalized),
            category=_category(concepts),
            summary=summary,
            concepts=concepts,
            related_terms_hi=tuple(hints.matched_terms),
            confidence=0.35 if concepts else None,
        )
