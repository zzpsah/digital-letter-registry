"""Preview-only rename mapping helpers.

This module generates proposed archive filenames. It never renames files and
contains no provider-specific Drive logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

from .naming import build_smart_filename


@dataclass(frozen=True, slots=True)
class RenameCandidate:
    original_filename: str
    short_title: str
    issuer: str
    issue_date: date | None = None
    reference_number: str | None = None


@dataclass(frozen=True, slots=True)
class RenamePreview:
    original_filename: str
    proposed_filename: str
    changed: bool


def build_rename_preview(
    candidates: Iterable[RenameCandidate],
) -> list[RenamePreview]:
    """Return a deterministic preview mapping without changing any file."""

    previews: list[RenamePreview] = []
    for candidate in candidates:
        proposed = build_smart_filename(
            short_title=candidate.short_title,
            issuer=candidate.issuer,
            issue_date=candidate.issue_date,
            reference_number=candidate.reference_number,
            original_filename=candidate.original_filename,
        )
        previews.append(
            RenamePreview(
                original_filename=candidate.original_filename,
                proposed_filename=proposed,
                changed=proposed != candidate.original_filename,
            )
        )
    return previews
