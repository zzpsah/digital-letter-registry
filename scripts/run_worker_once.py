"""Run at most one queued archive-processing job.

Designed for synthetic integration verification. Production daemon/service
deployment is intentionally out of scope until explicitly approved.
"""

from __future__ import annotations

import os

from letter_registry.extraction import VersionedTextExtractor
from letter_registry.autonomous_learning import AutonomousCorrectionMemory
from letter_registry.deterministic_context import DeterministicDocumentContextProvider
from letter_registry.extraction_backends import (
    OcrmypdfTesseractBackend,
    PypdfTextBackend,
    TesseractImageBackend,
)
from letter_registry.gemini_embeddings import GeminiEmbeddingProvider
from letter_registry.gemini_provider import GeminiDocumentContextProvider
from letter_registry.hermes_context_provider import HermesDefaultModelContextProvider
from letter_registry.supabase_gemini_gateway import SupabaseGeminiFileContextProvider
from letter_registry.google_drive_reader import GoogleDrivePrivateTransport
from letter_registry.jobs import SupabaseProcessingQueue
from letter_registry.original_access import SupabaseOriginalAccessService
from letter_registry.relationships import SupabaseRelationshipRepository
from letter_registry.semantic_search import SupabaseEmbeddingRepository
from letter_registry.self_healing import SelfHealingReprocessor
from letter_registry.versions import DICTIONARY_VERSION
from letter_registry.source_loader import SupabaseSourceLoader
from letter_registry.supabase_repository import SupabaseLetterRepository
from letter_registry.supabase_runtime import (
    ArchiveScopedSupabaseTransport,
    SupabasePostgrestTransport,
)
from letter_registry.worker import DocumentProcessingWorker


def _truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def main() -> int:
    transport = ArchiveScopedSupabaseTransport(
        transport=SupabasePostgrestTransport.from_worker_environment(),
        archive_id=os.environ["DLR_ARCHIVE_ID"],
    )
    repository = SupabaseLetterRepository(transport)
    queue = SupabaseProcessingQueue(transport)
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    gateway_configured = bool(
        os.environ.get("SUPABASE_GEMINI_GATEWAY_URL", "").strip()
        or os.environ.get("SUPABASE_GEMINI_PROJECT_URL", "").strip()
    )
    if gateway_configured:
        context_provider = SupabaseGeminiFileContextProvider.from_environment()
    elif gemini_key:
        context_provider = GeminiDocumentContextProvider.from_environment()
    else:
        context_provider = DeterministicDocumentContextProvider()
    embeddings = (
        SupabaseEmbeddingRepository(
            transport=transport,
            provider=GeminiEmbeddingProvider.from_environment(),
        )
        if gemini_key
        else None
    )

    if gateway_configured or gemini_key:
        healing = SelfHealingReprocessor(
            transport=transport,
            queue=queue,
        ).scan(
            target_context_version=str(getattr(context_provider, "version")),
            target_dictionary_version=DICTIONARY_VERSION,
            max_enqueues=int(os.environ.get("DLR_AUTO_REPROCESS_DAILY_LIMIT", "5")),
        )
        if healing.enqueued:
            print(f"self_healing_enqueued={healing.enqueued}")

    worker = DocumentProcessingWorker(
        queue=queue,
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
        context_provider=context_provider,
        fallback_context_provider=HermesDefaultModelContextProvider(),
        correction_memory=AutonomousCorrectionMemory.from_environment(),
        embeddings=embeddings,
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
