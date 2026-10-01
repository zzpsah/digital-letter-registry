"""Unicode-safe, derived smart-filename rules."""

from __future__ import annotations

import re
import unicodedata
from datetime import date
from pathlib import PurePath

_MAX_FILENAME_LENGTH = 220
_DASH_RUN = re.compile(r"-+")


def _normalise_part(
    value: str | None,
    *,
    lowercase: bool = True,
    placeholder: str | None = None,
) -> str:
    """Normalize one filename field while preserving Hindi/Unicode text."""

    text = unicodedata.normalize("NFC", (value or "").strip())
    output: list[str] = []
    pending_separator = False

    for char in text:
        category = unicodedata.category(char)
        if char.isalnum() or category.startswith("M"):
            if pending_separator and output and output[-1] != "-":
                output.append("-")
            output.append(char.lower() if lowercase else char)
            pending_separator = False
        else:
            pending_separator = True

    normalized = _DASH_RUN.sub("-", "".join(output)).strip("-")
    if normalized:
        return normalized
    if placeholder is not None:
        return placeholder
    raise ValueError("filename field must contain at least one letter or digit")


def build_smart_filename(
    *,
    short_title: str,
    issuer: str,
    issue_date: date | None,
    reference_number: str | None,
    original_filename: str,
) -> str:
    """Build the official derived archive filename.

    Pattern:
        short-title__issuer__date__reference-number.ext

    The original file is never mutated by this function.
    """

    extension = PurePath(original_filename).suffix
    if not extension:
        raise ValueError("original_filename must contain a file extension")

    title_part = _normalise_part(short_title)
    issuer_part = _normalise_part(issuer)
    date_part = issue_date.isoformat() if issue_date else "undated"
    reference_part = _normalise_part(
        reference_number,
        lowercase=False,
        placeholder="no-ref",
    )

    stem = "__".join((title_part, issuer_part, date_part, reference_part))
    max_stem_length = _MAX_FILENAME_LENGTH - len(extension)
    if max_stem_length < 1:
        raise ValueError("file extension is too long")

    stem = stem[:max_stem_length].rstrip("-_")
    return f"{stem}{extension}"
