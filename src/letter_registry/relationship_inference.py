"""Conservative deterministic relationship suggestions.

This layer creates reviewable suggestions only. It never confirms relationships
or changes status by itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher
import re

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
    issue_date: str | None = None


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
    "पूर्व आदेश को निरस्त",
    "पूर्व पत्र को निरस्त",
    "supersedes",
    "replaces previous",
    "in supersession of",
)
_REVISION_TERMS = (
    "पुनरीक्षित",
    "संशोधित",
    "संशोधन",
    "revised",
    "revision",
    "amended",
    "amendment",
    "corrigendum",
    "शुद्धि पत्र",
)


def _normalized(value: str | None) -> str:
    return " ".join((value or "").casefold().split())



def _tokens(value: str | None) -> set[str]:
    text = _normalized(value)
    return {
        token
        for token in re.findall(r"[\w\u0900-\u097f]+", text, flags=re.UNICODE)
        if len(token) >= 3
    }


def _similarity(left: str | None, right: str | None) -> float:
    a = _normalized(left)
    b = _normalized(right)
    if not a or not b:
        return 0.0
    seq = SequenceMatcher(None, a, b).ratio()
    at = _tokens(a)
    bt = _tokens(b)
    token = len(at & bt) / max(1, len(at | bt))
    return max(seq, token)


def _parse_iso_date(value: str | None) -> date | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _has_revision_cue(*values: str | None) -> bool:
    text = " ".join(_normalized(value) for value in values if value)
    return any(term in text for term in _REVISION_TERMS)


def _near_duplicate_suggestions(
    *,
    source_letter_id: str,
    source_reference_number: str | None,
    source_authority: str | None,
    source_category: str | None,
    source_title: str | None,
    source_summary: str | None,
    source_issue_date: str | None,
    source_text: str,
    candidates: list[RelationshipCandidate],
    version: str,
) -> list[RelationshipSuggestion]:
    rows: list[RelationshipSuggestion] = []
    src_ref = _normalized(source_reference_number)
    src_auth = _normalized(source_authority)
    src_cat = _normalized(source_category)
    src_date = _parse_iso_date(source_issue_date)
    revision_cue = _has_revision_cue(source_text, source_title, source_summary)

    for candidate in candidates:
        if candidate.record_id == source_letter_id:
            continue

        ref_match = bool(src_ref and src_ref == _normalized(candidate.reference_number))
        auth_match = bool(src_auth and src_auth == _normalized(candidate.authority))
        cat_match = bool(src_cat and src_cat == _normalized(candidate.category))
        title_sim = _similarity(source_title, candidate.title)
        summary_sim = _similarity(source_summary, candidate.summary)
        content_sim = max(title_sim, summary_sim)
        candidate_date = _parse_iso_date(candidate.issue_date)
        later_than_candidate = bool(
            src_date is not None and candidate_date is not None and src_date > candidate_date
        )

        if ref_match:
            # A later document with the same official reference and explicit
            # revision wording is much more likely to be a new authoritative
            # version than a duplicate scan. Keep it reviewable, but recommend
            # a supersede relationship.
            if (
                revision_cue
                and later_than_candidate
                and content_sim >= 0.50
                and content_sim < 0.995
            ):
                rows.append(
                    RelationshipSuggestion(
                        source_letter_id=source_letter_id,
                        target_letter_id=candidate.record_id,
                        relationship_type=DocumentRelationship.SUPERSEDES,
                        confidence=0.92 if (auth_match or not src_auth) else 0.84,
                        rationale=(
                            "Recommended supersede: same reference number, newer issue date, "
                            f"revision wording, and related content (score={content_sim:.2f})."
                        ),
                        version=version,
                    )
                )
            elif content_sim >= 0.92 and (auth_match or not src_auth):
                rows.append(
                    RelationshipSuggestion(
                        source_letter_id=source_letter_id,
                        target_letter_id=candidate.record_id,
                        relationship_type=DocumentRelationship.DUPLICATE_OF,
                        confidence=min(0.97, 0.91 + 0.04 * content_sim),
                        rationale=(
                            "Possible near-duplicate: same reference number with "
                            f"very high metadata/content similarity (score={content_sim:.2f}). "
                            "Requires review before treating as duplicate."
                        ),
                        version=version,
                    )
                )
            else:
                rows.append(
                    RelationshipSuggestion(
                        source_letter_id=source_letter_id,
                        target_letter_id=candidate.record_id,
                        relationship_type=DocumentRelationship.RELATED_TO,
                        confidence=0.86 if (later_than_candidate and auth_match) else (0.82 if auth_match else 0.74),
                        rationale=(
                            "Possible revised/versioned document: same reference number "
                            f"with materially different content (score={content_sim:.2f}). "
                            + (
                                "The incoming document is newer. "
                                if later_than_candidate
                                else ""
                            )
                            + "Review before changing version status."
                        ),
                        version=version,
                    )
                )
            continue

        # Without a reference match, require a much stronger metadata agreement.
        if auth_match and cat_match and title_sim >= 0.94 and summary_sim >= 0.86:
            rows.append(
                RelationshipSuggestion(
                    source_letter_id=source_letter_id,
                    target_letter_id=candidate.record_id,
                    relationship_type=DocumentRelationship.DUPLICATE_OF,
                    confidence=0.88,
                    rationale=(
                        "Possible near-duplicate without reference number: same authority/category "
                        f"and very high title/summary similarity (title={title_sim:.2f}, summary={summary_sim:.2f}). "
                        "Requires human review."
                    ),
                    version=version,
                )
            )

    return rows


def infer_relationship_suggestions(
    *,
    source_letter_id: str,
    source_reference_number: str | None,
    source_authority: str | None,
    source_category: str | None,
    source_text: str,
    candidates: list[RelationshipCandidate],
    source_title: str | None = None,
    source_summary: str | None = None,
    source_issue_date: str | None = None,
    version: str = "relationship-inference-v3",
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
        return _near_duplicate_suggestions(
            source_letter_id=source_letter_id,
            source_reference_number=source_reference_number,
            source_authority=source_authority,
            source_category=source_category,
            source_title=source_title,
            source_summary=source_summary,
            source_issue_date=source_issue_date,
            source_text=source_text,
            candidates=candidates,
            version=version,
        )

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
