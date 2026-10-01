"""Safe, derived smart-filename rules."""

from __future__ import annotations

import re
import unicodedata
from datetime import date
from pathlib import PurePath

_MAX_STEM_LENGTH = 120
_UNSAFE = re.compile(r"[^A-Za-z0-9]+")
_DASH_RUN = re.compile(r"-+")


def _normalise_part(value: str) -> str:
    normalised = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    normalised = _UNSAFE.sub("-", normalised).strip("-").lower()
    return _DASH_RUN.sub("-", normalised)


def build_smart_filename(
    *,
    issue_date: date | None,
    category: str,
    subject: str,
    original_filename: str,
    letter_number: str | None = None,
    record_suffix: str | None = None,
) -> str:
    """Build a deterministic derived filename while preserving no original content."""

    extension = PurePath(original_filename).suffix.lower() or ".bin"
    date_part = issue_date.isoformat() if issue_date else "undated"
    parts = [date_part, _normalise_part(category), _normalise_part(subject)]
    if letter_number:
        parts.append(_normalise_part(letter_number))
    if record_suffix:
        parts.append(_normalise_part(record_suffix))
    cleaned = [part for part in parts if part]
    if len(cleaned) < 3:
        raise ValueError("category and subject must contain usable characters")
    stem = "_".join(cleaned)[:_MAX_STEM_LENGTH].rstrip("_")
    return f"{stem}{extension}"
