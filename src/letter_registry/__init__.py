"""Provider-independent domain rules for Digital Letter Registry."""

from .context_hints import ContextHints, detect_context_hints
from .extraction import (
    ExtractionResult,
    OcrBackend,
    PdfTextBackend,
    VersionedTextExtractor,
    is_usable_native_text,
    normalize_extracted_text,
)
from .extraction_backends import OcrmypdfTesseractBackend, PypdfTextBackend
from .fingerprints import sha256_file
from .gemini_provider import GeminiDocumentContextProvider, GeminiProviderError
from .ingestion import prepare_source_record, persist_prepared_source
from .orchestration import ingest_original
from .processing_pipeline import ProcessingOutcome, process_archived_document
from .models import (
    DocumentRecord,
    DocumentRelationship,
    DocumentStatus,
    ProcessingVersions,
)
from .naming import build_smart_filename
from .persistence import (
    InMemoryLetterRepository,
    LetterRepository,
    build_supabase_letter_row,
    build_supabase_processing_row,
)
from .rename_preview import (
    RenameCandidate,
    RenamePreview,
    build_rename_preview,
    render_rename_preview_csv,
)
from .storage import (
    GoogleDriveOriginalStorage,
    GoogleDriveTransport,
    InMemoryOriginalStorage,
    OriginalStorage,
    StoredOriginal,
)
from .supabase_repository import SupabaseLetterRepository, SupabaseTransport
from .supabase_runtime import SupabasePostgrestTransport, SupabaseRuntimeError

__all__ = [
    "ContextHints",
    "ExtractionResult",
    "PdfTextBackend",
    "OcrBackend",
    "VersionedTextExtractor",
    "PypdfTextBackend",
    "OcrmypdfTesseractBackend",
    "GeminiDocumentContextProvider",
    "GeminiProviderError",
    "DocumentRecord",
    "DocumentRelationship",
    "DocumentStatus",
    "ProcessingVersions",
    "RenameCandidate",
    "RenamePreview",
    "LetterRepository",
    "InMemoryLetterRepository",
    "StoredOriginal",
    "OriginalStorage",
    "InMemoryOriginalStorage",
    "GoogleDriveTransport",
    "GoogleDriveOriginalStorage",
    "prepare_source_record",
    "ingest_original",
    "ProcessingOutcome",
    "process_archived_document",
    "persist_prepared_source",
    "SupabaseTransport",
    "SupabaseLetterRepository",
    "SupabasePostgrestTransport",
    "SupabaseRuntimeError",
    "detect_context_hints",
    "is_usable_native_text",
    "normalize_extracted_text",
    "build_rename_preview",
    "build_smart_filename",
    "build_supabase_letter_row",
    "build_supabase_processing_row",
    "render_rename_preview_csv",
    "sha256_file",
]
