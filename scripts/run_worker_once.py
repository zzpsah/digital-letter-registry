"""Run at most one queued archive-processing job.

Designed for synthetic integration verification. Production daemon/service
deployment is intentionally out of scope until explicitly approved.
"""

from __future__ import annotations

import os

from letter_registry.extraction import VersionedTextExtractor
from letter_registry.extraction_backends import (
    OcrmypdfTesseractBackend,
    PypdfTextBackend,
    TesseractImageBackend,
)
from letter_registry.gemini_embeddings import GeminiEmbeddingProvider
from letter_registry.gemini_provider import GeminiDocumentContextProvider
from letter_registry.google_drive_reader import GoogleDrivePrivateTransport
from letter_registry.jobs import SupabaseProcessingQueue
from letter_registry.original_access import SupabaseOriginalAccessService
from letter_registry.relationships import SupabaseRelationshipRepository
from letter_registry.semantic_search import SupabaseEmbeddingRepository
from letter_registry.source_loader import SupabaseSourceLoader
from letter_registry.supabase_repository import SupabaseLetterRepository
from letter_registry.supabase_runtime import SupabasePostgrestTransport
from letter_registry.worker import DocumentProcessingWorker


def _truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def main() -> int:
    transport = SupabasePostgrestTransport.from_environment()
    repository = SupabaseLetterRepository(transport)
    embedding_provider = GeminiEmbeddingProvider.from_environment()

    worker = DocumentProcessingWorker(
        queue=SupabaseProcessingQueue(transport),
        source_loader=SupabaseSourceLoader(transport),
        database=transport,
        original_access=SupabaseOriginalAccessService(
            GoogleDrivePrivateTransport.from_environment()
        ),
        repository=repository,
        extractor=VersionedTextExtractor(
            pdf_backend=PypdfTextBackend(),
            ocr_backend=OcrmypdfTesseractBackend(),
            image_ocr_backend=TesseractImageBackend(),
        ),
        context_provider=GeminiDocumentContextProvider.from_environment(),
        embeddings=SupabaseEmbeddingRepository(
            transport=transport,
            provider=embedding_provider,
        ),
        relationship_repository=SupabaseRelationshipRepository(transport),
        allow_real_documents=_truthy("ENABLE_REAL_INTAKE"),
    )

    result = worker.run_once()
    print(f"status={result.status}")
    if result.job_id:
        print(f"job_id={result.job_id}")
    if result.letter_id:
        print(f"letter_id={result.letter_id}")
    if result.status == "completed":
        print(f"chunks={result.chunks}")
        return 0
    if result.status == "idle":
        return 0

    print(f"error={result.error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
