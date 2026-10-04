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


def _mime_type_for_path(path: Path) -> str:
    return {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(path.suffix.lower(), "application/octet-stream")


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
    fallback_context_provider: DocumentContextProvider | None = None,
    intake_context: str = "",
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

    analysis_text = extraction.text
    intake_context = " ".join(str(intake_context or "").split()).strip()
    if intake_context:
        analysis_text += (
            "\n\n[INTAKE MESSAGE / SENDER INSTRUCTION — not document evidence]\n"
            + intake_context
        )

    try:
        analyze_file = getattr(context_provider, "analyze_file", None)
        if callable(analyze_file):
            from dataclasses import replace
            from .context_hints import detect_context_hints

            hints = detect_context_hints(analysis_text)
            direct_context = analyze_file(
                file_bytes=Path(path).read_bytes(),
                mime_type=_mime_type_for_path(Path(path)),
                filename=Path(path).name,
                extracted_text=analysis_text,
                hints=hints,
            )
            merged_concepts = tuple(dict.fromkeys((*hints.concepts, *direct_context.concepts)))
            if merged_concepts != direct_context.concepts:
                direct_context = replace(direct_context, concepts=merged_concepts)
            context = ContextAnalysisResult(
                context=direct_context,
                hints=hints,
                version=str(getattr(context_provider, "version")),
            )
        else:
            context = analyze_document_context(
                analysis_text,
                provider=context_provider,
            )
    except Exception:
        if fallback_context_provider is None:
            raise
        context = analyze_document_context(
            analysis_text,
            provider=fallback_context_provider,
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
