"""Provider-independent domain rules for Digital Letter Registry."""

from .fingerprints import sha256_file
from .ingestion import prepare_source_record, persist_prepared_source
from .orchestration import ingest_original
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

__all__ = [
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
    "persist_prepared_source",
    "SupabaseTransport",
    "SupabaseLetterRepository",
    "build_rename_preview",
    "build_smart_filename",
    "build_supabase_letter_row",
    "build_supabase_processing_row",
    "render_rename_preview_csv",
    "sha256_file",
]
