"""Deterministic structured context fallback when no AI provider is configured.

The fallback is intentionally conservative. It derives only broad labels from
the checked-in vocabulary and never invents dates, reference numbers, deadlines,
or specific actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re

from .context_hints import ContextHints
from .extraction import normalize_extracted_text
from .structured_analysis import StructuredDocumentContext


def _explicit_authority(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        folded = stripped.casefold()
        if "जिला शिक्षा पदाधिकारी" in folded:
            return stripped[:160]
    return None


def _explicit_reference_number(text: str) -> str | None:
    match = re.search(
        r"\b[A-Z]{2,}[A-Za-z0-9.]*"
        r"(?:/[A-Za-z0-9.]+){2,}/\d{4}/\d+\b",
        text,
    )
    return match.group(0) if match else None


def _explicit_issue_date(text: str) -> str | None:
    match = re.search(
        r"दिनांक\s*[:：]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
        text,
    )
    if not match:
        return None
    raw = match.group(1).replace("-", "/")
    try:
        return datetime.strptime(raw, "%d/%m/%Y").date().isoformat()
    except ValueError:
        return None


def _authority(text: str) -> str | None:
    explicit = _explicit_authority(text)
    if explicit:
        return explicit

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


def _explicit_title(text: str) -> str | None:
    folded = text.casefold()
    if "स्थानांतरण" in folded and "पदस्थापन" in folded and "आदेश" in folded:
        return "स्थानांतरण / पदस्थापन आदेश"
    return None


def _explicit_category(text: str) -> str | None:
    folded = text.casefold()
    if "स्थानांतरण" in folded and "पदस्थापन" in folded:
        return "transfer-posting"
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

    version: str = "deterministic:hints-v2"
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
        explicit_title = _explicit_title(normalized)
        explicit_category = _explicit_category(normalized)
        authority = _authority(normalized)
        reference_number = _explicit_reference_number(normalized)
        issue_date = _explicit_issue_date(normalized)
        explicit_facts = sum(
            value is not None
            for value in (
                explicit_title,
                explicit_category,
                authority,
                reference_number,
                issue_date,
            )
        )
        return StructuredDocumentContext(
            title=explicit_title or _title(concepts),
            authority=authority,
            category=explicit_category or _category(concepts),
            summary=summary,
            issue_date=issue_date,
            reference_number=reference_number,
            concepts=concepts,
            related_terms_hi=tuple(hints.matched_terms),
            confidence=(
                min(0.8, 0.45 + 0.07 * explicit_facts)
                if explicit_facts
                else (0.35 if concepts else None)
            ),
        )
