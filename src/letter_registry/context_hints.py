"""Deterministic context hints before AI analysis."""

from __future__ import annotations

from dataclasses import dataclass

from .extraction import normalize_extracted_text
from .vocabulary import CONCEPT_RULES, STRUCTURE_TERMS


@dataclass(frozen=True, slots=True)
class ContextHints:
    concepts: tuple[str, ...]
    matched_terms: tuple[str, ...]
    structure_terms: tuple[str, ...]


def detect_context_hints(text: str) -> ContextHints:
    normalized = normalize_extracted_text(text)
    haystack = f" {normalized.casefold()} "

    concepts: list[str] = []
    matched_terms: list[str] = []

    for rule in CONCEPT_RULES:
        hits = [term for term in rule.terms if term.casefold() in haystack]
        if hits:
            concepts.append(rule.concept)
            matched_terms.extend(hits)

    structure_hits = [
        term for term in STRUCTURE_TERMS if term.casefold() in haystack
    ]

    return ContextHints(
        concepts=tuple(dict.fromkeys(concepts)),
        matched_terms=tuple(dict.fromkeys(matched_terms)),
        structure_terms=tuple(dict.fromkeys(structure_hits)),
    )
