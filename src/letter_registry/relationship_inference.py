"""Conservative deterministic relationship suggestions.

This layer creates reviewable suggestions only. It never confirms relationships
or changes status by itself.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import DocumentRelationship
from .relationships import RelationshipSuggestion


@dataclass(frozen=True, slots=True)
class RelationshipCandidate:
    record_id: str
    reference_number: str | None
    authority: str | None
    category: str | None
    title: str | None
    summary: str | None


_EXTEND_TERMS = (
    "तिथि विस्तार",
    "अवधि विस्तार",
    "extended",
    "extension",
    "last date extended",
)
_CORRECT_TERMS = (
    "शुद्धि पत्र",
    "संशोधन",
    "corrigendum",
    "correction",
    "revised correction",
)
_SUPERSEDE_TERMS = (
    "पूर्व आदेश निरस्त",
    "पूर्व पत्र निरस्त",
    "supersedes",
    "replaces previous",
)


def _normalized(value: str | None) -> str:
    return " ".join((value or "").casefold().split())


def infer_relationship_suggestions(
    *,
    source_letter_id: str,
    source_reference_number: str | None,
    source_authority: str | None,
    source_category: str | None,
    source_text: str,
    candidates: list[RelationshipCandidate],
    version: str = "explicit-reference-rules-v1",
) -> list[RelationshipSuggestion]:
    """Suggest only when explicit relationship wording + a reference match exist."""

    text = _normalized(source_text)
    relation: DocumentRelationship | None = None
    cue = ""

    for term in _SUPERSEDE_TERMS:
        if term in text:
            relation = DocumentRelationship.SUPERSEDES
            cue = term
            break
    if relation is None:
        for term in _CORRECT_TERMS:
            if term in text:
                relation = DocumentRelationship.CORRECTS
                cue = term
                break
    if relation is None:
        for term in _EXTEND_TERMS:
            if term in text:
                relation = DocumentRelationship.EXTENDS
                cue = term
                break

    if relation is None:
        return []

    suggestions: list[RelationshipSuggestion] = []
    for candidate in candidates:
        if candidate.record_id == source_letter_id:
            continue
        ref = _normalized(candidate.reference_number)
        if not ref or ref not in text:
            continue

        confidence = 0.94
        if source_authority and candidate.authority:
            if _normalized(source_authority) != _normalized(candidate.authority):
                confidence -= 0.15
        if source_category and candidate.category:
            if _normalized(source_category) != _normalized(candidate.category):
                confidence -= 0.10

        suggestions.append(
            RelationshipSuggestion(
                source_letter_id=source_letter_id,
                target_letter_id=candidate.record_id,
                relationship_type=relation,
                confidence=max(0.0, confidence),
                rationale=(
                    f"Explicit cue '{cue}' and referenced prior letter "
                    f"'{candidate.reference_number}'."
                ),
                version=version,
            )
        )
    return suggestions
