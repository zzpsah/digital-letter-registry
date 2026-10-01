"""Preview-only rename mapping helpers.

This module generates proposed archive filenames. It never renames files and
contains no provider-specific Drive logic.
"""

from __future__ import annotations

import csv
import io
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


def render_rename_preview_csv(previews: Iterable[RenamePreview]) -> str:
    """Render a reviewable CSV report; performs no rename or provider write."""

    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(("original_filename", "proposed_filename", "changed"))
    for preview in previews:
        writer.writerow(
            (
                preview.original_filename,
                preview.proposed_filename,
                "yes" if preview.changed else "no",
            )
        )
    return buffer.getvalue()
