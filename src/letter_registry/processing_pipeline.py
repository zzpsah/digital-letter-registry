"""End-to-end derived processing orchestration for one archived document."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .extraction import ExtractionResult, VersionedTextExtractor
from .models import DocumentRecord
from .structured_analysis import (
    ContextAnalysisResult,
    DocumentContextProvider,
    analyze_document_context,
)


class ProcessingRepository:
    """Narrow repository shape needed by derived processing."""

    def save_extraction_result(
        self,
        record: DocumentRecord,
        *,
        owner_id: str,
        result: ExtractionResult,
    ) -> None:
        ...

    def save_context_result(
        self,
        record: DocumentRecord,
        *,
        owner_id: str,
        result: ContextAnalysisResult,
    ) -> None:
        ...


@dataclass(frozen=True, slots=True)
class ProcessingOutcome:
    extraction: ExtractionResult
    context: ContextAnalysisResult


def process_archived_document(
    path: str | Path,
    *,
    record: DocumentRecord,
    owner_id: str,
    extractor: VersionedTextExtractor,
    context_provider: DocumentContextProvider,
    repository: ProcessingRepository,
) -> ProcessingOutcome:
    """Process one already-archived source without mutating the original."""

    extraction = extractor.extract(path)
    repository.save_extraction_result(
        record,
        owner_id=owner_id,
        result=extraction,
    )

    if not extraction.text.strip():
        raise RuntimeError("cannot analyze document context without extracted text")

    context = analyze_document_context(
        extraction.text,
        provider=context_provider,
    )
    repository.save_context_result(
        record,
        owner_id=owner_id,
        result=context,
    )

    return ProcessingOutcome(
        extraction=extraction,
        context=context,
    )
