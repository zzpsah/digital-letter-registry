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
    folded_all = text.casefold()
    if (
        "central board of secondary education" in folded_all
        or "केन्द्रीय माध्यमिक शिक्षा बोर्ड" in folded_all
        or "केंद्रीय माध्यमिक शिक्षा बोर्ड" in folded_all
    ):
        return "CBSE"

    for line in text.splitlines():
        stripped = line.strip()
        folded = stripped.casefold()
        if "जिला शिक्षा पदाधिकारी" in folded:
            return stripped[:160]
    return None


def _explicit_reference_number(text: str) -> str | None:
    # Deterministic fallback must identify the current document's own header,
    # not a prior memo/reference merely cited in the body.
    cbse_match = re.search(
        r"^\s*(CBSE/[A-Za-z0-9.]+(?:/[A-Za-z0-9.]+)+/\d{4})\b",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if cbse_match:
        return cbse_match.group(1)

    header = re.compile(
        r"^\s*(?:पत्रांक|पंत्रांक|ज्ञापांक|memo(?:\s+no\.?)?|reference|ref\.?|letter\s+no\.?)"
        r"\s*[:：-]?\s*([^\s]+)",
        flags=re.IGNORECASE,
    )
    for line in text.splitlines():
        match = header.match(line)
        if not match:
            continue
        candidate = match.group(1).strip(" .,:;-")
        alnum = re.sub(r"[^A-Za-z0-9\u0900-\u097f]", "", candidate)
        if len(alnum) < 2:
            continue
        if re.fullmatch(r"[.\-_/():;]+", candidate):
            continue
        return candidate[:120]
    return None


def _explicit_issue_date(text: str) -> str | None:
    date_pattern = re.compile(
        r"(?:दिनांक|dated?)\s*[:：]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{4})",
        flags=re.IGNORECASE,
    )
    header_start = re.compile(
        r"^\s*(?:पत्रांक|पंत्रांक|ज्ञापांक|memo(?:\s+no\.?)?|reference|ref\.?|letter\s+no\.?|CBSE/)",
        flags=re.IGNORECASE,
    )
    for line in text.splitlines():
        if not header_start.match(line):
            continue
        match = date_pattern.search(line)
        if not match:
            continue
        raw = match.group(1).replace("-", "/").replace(".", "/")
        try:
            return datetime.strptime(raw, "%d/%m/%Y").date().isoformat()
        except ValueError:
            continue
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
    if (
        "central board of secondary education" in folded
        and "affiliation" in folded
        and "notification" in folded
    ):
        return "CBSE Affiliation Notification"
    if "स्थानांतरण" in folded and "पदस्थापन" in folded and "आदेश" in folded:
        return "स्थानांतरण / पदस्थापन आदेश"
    return None


def _explicit_category(text: str) -> str | None:
    folded = text.casefold()
    if (
        "central board of secondary education" in folded
        and ("affiliation" in folded or "saras" in folded)
    ):
        return "affiliation"
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
    return None



@dataclass(frozen=True, slots=True)
class DeterministicDocumentContextProvider:
    """Vocabulary-only fallback suitable for OCR/full-text indexing."""

    version: str = "deterministic:hints-v3"
    summary_characters: int = 280

    def analyze(
        self,
        *,
        extracted_text: str,
        hints: ContextHints,
    ) -> StructuredDocumentContext:
        normalized = normalize_extracted_text(extracted_text)
        summary = None
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
