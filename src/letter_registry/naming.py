"""Unicode-safe, derived smart-filename rules."""

from __future__ import annotations

import re
import unicodedata
from datetime import date
from pathlib import PurePath

FILENAME_RULE_VERSION = "official-v1"

_MAX_FILENAME_LENGTH = 220
_MAX_TITLE_LENGTH = 90
_MAX_ISSUER_LENGTH = 60
_MAX_REFERENCE_LENGTH = 40
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


def _limit_field(value: str, max_length: int) -> str:
    """Trim a normalized field without removing the canonical separators later."""

    trimmed = value[:max_length].rstrip("-")
    if not trimmed:
        raise ValueError("filename field became empty after length normalization")
    return trimmed


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

    title_part = _limit_field(_normalise_part(short_title), _MAX_TITLE_LENGTH)
    issuer_part = _limit_field(_normalise_part(issuer), _MAX_ISSUER_LENGTH)
    date_part = issue_date.isoformat() if issue_date else "undated"
    reference_part = _limit_field(
        _normalise_part(
            reference_number,
            lowercase=False,
            placeholder="no-ref",
        ),
        _MAX_REFERENCE_LENGTH,
    )

    stem = "__".join((title_part, issuer_part, date_part, reference_part))
    filename = f"{stem}{extension}"
    if len(filename) > _MAX_FILENAME_LENGTH:
        raise ValueError("derived filename exceeds the configured safe length")
    return filename
