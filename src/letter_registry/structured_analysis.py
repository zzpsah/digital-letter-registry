"""Structured document-analysis contracts.

AI providers must return this provider-neutral shape. Deterministic context hints
can be merged in before/after an AI call without changing the storage schema.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Protocol

from .context_hints import ContextHints, detect_context_hints


@dataclass(frozen=True, slots=True)
class ImportantDate:
    label: str
    value: str
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class StructuredDocumentContext:
    title: str | None = None
    authority: str | None = None
    category: str | None = None
    subcategory: str | None = None
    summary: str | None = None
    action_required: str | None = None
    issue_date: str | None = None
    reference_number: str | None = None
    concepts: tuple[str, ...] = ()
    important_dates: tuple[ImportantDate, ...] = ()
    deadline: str | None = None
    related_terms_hi: tuple[str, ...] = ()
    related_terms_en: tuple[str, ...] = ()
    confidence: float | None = None
    key_points: tuple[str, ...] = ()
    clean_document_text: str | None = None
    quality_score: float | None = None
    quality_flags: tuple[str, ...] = ()
    needs_reprocessing: bool = False
    quality_version: str | None = None

    def to_json_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["concepts"] = list(self.concepts)
        data["important_dates"] = [asdict(item) for item in self.important_dates]
        data["related_terms_hi"] = list(self.related_terms_hi)
        data["related_terms_en"] = list(self.related_terms_en)
        data["quality_flags"] = list(self.quality_flags)
        return data


class DocumentFileContextProvider(Protocol):
    """Optional provider capability for direct PDF/image understanding."""

    version: str

    def analyze_file(
        self,
        *,
        file_bytes: bytes,
        mime_type: str,
        filename: str,
        extracted_text: str,
        hints: ContextHints,
    ) -> StructuredDocumentContext:
        ...


class DocumentContextProvider(Protocol):
    """Replaceable AI/provider contract for structured document understanding."""

    version: str

    def analyze(
        self,
        *,
        extracted_text: str,
        hints: ContextHints,
    ) -> StructuredDocumentContext:
        ...


@dataclass(frozen=True, slots=True)
class ContextAnalysisResult:
    context: StructuredDocumentContext
    hints: ContextHints
    version: str


def analyze_document_context(
    extracted_text: str,
    *,
    provider: DocumentContextProvider,
) -> ContextAnalysisResult:
    hints = detect_context_hints(extracted_text)
    context = provider.analyze(extracted_text=extracted_text, hints=hints)

    merged_concepts = tuple(
        dict.fromkeys((*hints.concepts, *context.concepts))
    )
    if merged_concepts != context.concepts:
        context = StructuredDocumentContext(
            title=context.title,
            authority=context.authority,
            category=context.category,
            subcategory=context.subcategory,
            summary=context.summary,
            action_required=context.action_required,
            issue_date=context.issue_date,
            reference_number=context.reference_number,
            concepts=merged_concepts,
            important_dates=context.important_dates,
            deadline=context.deadline,
            related_terms_hi=context.related_terms_hi,
            related_terms_en=context.related_terms_en,
            confidence=context.confidence,
            key_points=context.key_points,
            clean_document_text=context.clean_document_text,
            quality_score=context.quality_score,
            quality_flags=context.quality_flags,
            needs_reprocessing=context.needs_reprocessing,
            quality_version=context.quality_version,
        )

    return ContextAnalysisResult(
        context=context,
        hints=hints,
        version=provider.version,
    )
