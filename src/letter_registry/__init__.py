"""Provider-independent domain rules for Digital Letter Registry."""

from .fingerprints import sha256_file
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
    "SupabaseTransport",
    "SupabaseLetterRepository",
    "build_rename_preview",
    "build_smart_filename",
    "build_supabase_letter_row",
    "build_supabase_processing_row",
    "render_rename_preview_csv",
    "sha256_file",
]
