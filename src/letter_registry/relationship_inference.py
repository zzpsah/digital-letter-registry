"""Conservative deterministic relationship suggestions.

This layer creates reviewable suggestions only. It never confirms relationships
or changes status by itself.
"""

from __future__ import annotations

from dataclasses import dataclass
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


def _near_duplicate_suggestions(
    *,
    source_letter_id: str,
    source_reference_number: str | None,
    source_authority: str | None,
    source_category: str | None,
    source_title: str | None,
    source_summary: str | None,
    candidates: list[RelationshipCandidate],
    version: str,
) -> list[RelationshipSuggestion]:
    rows: list[RelationshipSuggestion] = []
    src_ref = _normalized(source_reference_number)
    src_auth = _normalized(source_authority)
    src_cat = _normalized(source_category)

    for candidate in candidates:
        if candidate.record_id == source_letter_id:
            continue

        ref_match = bool(src_ref and src_ref == _normalized(candidate.reference_number))
        auth_match = bool(src_auth and src_auth == _normalized(candidate.authority))
        cat_match = bool(src_cat and src_cat == _normalized(candidate.category))
        title_sim = _similarity(source_title, candidate.title)
        summary_sim = _similarity(source_summary, candidate.summary)
        content_sim = max(title_sim, summary_sim)

        if ref_match:
            # Same official reference is strong identity evidence, but not enough
            # to silently collapse documents: revised/corrected scans can reuse it.
            if content_sim >= 0.88 and (auth_match or not src_auth):
                rows.append(
                    RelationshipSuggestion(
                        source_letter_id=source_letter_id,
                        target_letter_id=candidate.record_id,
                        relationship_type=DocumentRelationship.DUPLICATE_OF,
                        confidence=min(0.97, 0.90 + 0.05 * content_sim),
                        rationale=(
                            "Possible near-duplicate: same reference number with "
                            f"high metadata/content similarity (score={content_sim:.2f}). "
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
                        confidence=0.84 if auth_match else 0.76,
                        rationale=(
                            "Possible revised/versioned document: same reference number "
                            f"but materially different title/summary similarity (score={content_sim:.2f}). "
                            "Review as revised copy, correction, or separate issuance."
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
    version: str = "relationship-inference-v2",
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
