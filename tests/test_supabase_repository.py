from datetime import datetime, timezone
import unittest

from letter_registry.models import DocumentRecord
from letter_registry.supabase_repository import SupabaseLetterRepository


OWNER_ID = "11111111-1111-4111-8111-111111111111"
LETTER_ID = "22222222-2222-4222-8222-222222222222"


class FakeTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, object], str | None]] = []

    def insert(
        self,
        table: str,
        row: dict[str, object],
        *,
        on_conflict: str | None = None,
    ) -> dict[str, object]:
        self.calls.append(("insert", table, row, on_conflict))
        return row

    def upsert(
        self,
        table: str,
        row: dict[str, object],
        *,
        on_conflict: str,
    ) -> dict[str, object]:
        self.calls.append(("upsert", table, row, on_conflict))
        return row

    def update(
        self,
        table: str,
        row: dict[str, object],
        *,
        filters: dict[str, str],
    ) -> dict[str, object]:
        self.calls.append(("update", table, row, str(filters)))
        return row


def record() -> DocumentRecord:
    return DocumentRecord(
        record_id=LETTER_ID,
        original_filename="synthetic.pdf",
        original_sha256="a" * 64,
        original_storage_reference="synthetic-private-object",
        received_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
    )


class SupabaseRepositoryTests(unittest.TestCase):
    def test_rename_identity_lookup_stays_server_side(self) -> None:
        class IdentityTransport(FakeTransport):
            def select(self, table, *, filters=None, columns="*"):
                return [{
                    "id": LETTER_ID,
                    "original_filename": "DOC10086.pdf",
                    "storage_provider": "gdrive",
                    "storage_object_id": "private-object-reference",
                }]

        repository = SupabaseLetterRepository(IdentityTransport())
        identity = repository.get_rename_identity(LETTER_ID)

        self.assertEqual(identity.record_id, LETTER_ID)
        self.assertEqual(identity.original_filename, "DOC10086.pdf")
        self.assertEqual(identity.storage_provider, "gdrive")
        self.assertEqual(
            identity.storage_object_reference,
            "private-object-reference",
        )

    def test_source_insert_targets_letters_with_duplicate_conflict_key(self) -> None:
        transport = FakeTransport()
        repository = SupabaseLetterRepository(transport)

        repository.save_source(record(), owner_id=OWNER_ID)

        method, table, row, conflict = transport.calls[0]
        self.assertEqual(method, "insert")
        self.assertEqual(table, "letters")
        self.assertEqual(conflict, "owner_id,original_sha256")
        self.assertEqual(row["owner_id"], OWNER_ID)
        self.assertEqual(row["storage_provider"], "gdrive")

    def test_processing_state_is_upserted_by_letter_id(self) -> None:
        transport = FakeTransport()
        repository = SupabaseLetterRepository(transport)

        repository.save_processing_state(record(), owner_id=OWNER_ID)

        method, table, row, conflict = transport.calls[0]
        self.assertEqual(method, "upsert")
        self.assertEqual(table, "letter_processing")
        self.assertEqual(conflict, "letter_id")
        self.assertEqual(row["letter_id"], LETTER_ID)

    def test_context_save_updates_existing_letter_row(self) -> None:
        from unittest.mock import patch

        transport = FakeTransport()
        repository = SupabaseLetterRepository(transport)

        with patch(
            "letter_registry.supabase_repository.build_supabase_context_processing_patch",
            return_value={"letter_id": LETTER_ID, "owner_id": OWNER_ID},
        ), patch(
            "letter_registry.supabase_repository.build_supabase_letter_context_patch",
            return_value={"id": LETTER_ID, "owner_id": OWNER_ID, "title": "Synthetic"},
        ):
            repository.save_context_result(
                record(),
                owner_id=OWNER_ID,
                result=object(),
            )

        self.assertEqual(transport.calls[0][0], "upsert")
        self.assertEqual(transport.calls[0][1], "letter_processing")
        self.assertEqual(transport.calls[1][0], "update")
        self.assertEqual(transport.calls[1][1], "letters")
        self.assertIn(LETTER_ID, transport.calls[1][3])

    def test_direct_gemini_migration_replaces_unreviewed_gateway_metadata(self) -> None:
        from unittest.mock import patch
        from letter_registry.context_hints import detect_context_hints
        from letter_registry.structured_analysis import ContextAnalysisResult, StructuredDocumentContext

        class ExistingTransport(FakeTransport):
            def select(self, table, *, filters=None, columns="*"):
                if table == "letters":
                    return [{
                        "title": "Old title", "authority": "Old authority",
                        "category": "Old category", "subcategory": None,
                        "summary": "Old summary", "reference_number": "OLD-REF",
                        "issue_date": "2025-06-02", "action_required": None,
                    }]
                if table == "letter_processing":
                    return [{
                        "structured_context": {"confidence": 1.0, "summary_hi": "पुराना सारांश"},
                        "context_version": "supabase-gemini:gemini-3.5-flash-lite:document-v3",
                        "reviewed_at": None,
                    }]
                return []

        transport = ExistingTransport()
        repository = SupabaseLetterRepository(transport)
        result = ContextAnalysisResult(
            context=StructuredDocumentContext(
                title="New source-grounded title", authority="New authority",
                category="New category", summary="New source-grounded summary",
                reference_number="NEW-REF", issue_date="2026-08-18",
                summary_hi="नया सारांश", confidence=0.95,
            ),
            hints=detect_context_hints("synthetic source text"),
            version="gemini:gemini-3.5-flash-lite:context-v3",
        )
        captured = {}
        with patch(
            "letter_registry.supabase_repository.build_supabase_context_processing_patch",
            side_effect=lambda record, *, owner_id, result: (captured.__setitem__("result", result) or {}),
        ), patch(
            "letter_registry.supabase_repository.build_supabase_letter_context_patch",
            return_value={"id": LETTER_ID, "owner_id": OWNER_ID},
        ):
            repository.save_context_result(record(), owner_id=OWNER_ID, result=result)

        saved = captured["result"].context
        self.assertEqual(saved.title, "New source-grounded title")
        self.assertEqual(saved.reference_number, "NEW-REF")
        self.assertEqual(saved.issue_date, "2026-08-18")

    def test_same_version_direct_gemini_refresh_replaces_stale_unreviewed_metadata(self) -> None:
        from unittest.mock import patch
        from letter_registry.context_hints import detect_context_hints
        from letter_registry.structured_analysis import ContextAnalysisResult, StructuredDocumentContext

        class ExistingDirectTransport(FakeTransport):
            def select(self, table, *, filters=None, columns="*"):
                if table == "letters":
                    return [{
                        "title": "Stale AI title", "authority": "Stale authority",
                        "category": "Stale category", "subcategory": None,
                        "summary": "Stale summary", "reference_number": "STALE-REF",
                        "issue_date": "2025-06-02", "action_required": None,
                    }]
                if table == "letter_processing":
                    return [{
                        "structured_context": {"confidence": 1.0},
                        "context_version": "gemini:gemini-3.5-flash-lite:context-v3",
                        "reviewed_at": None,
                    }]
                return []

        transport = ExistingDirectTransport()
        repository = SupabaseLetterRepository(transport)
        result = ContextAnalysisResult(
            context=StructuredDocumentContext(
                title="Corrected source title", authority="Corrected authority",
                category="Corrected category", summary="Corrected source summary",
                reference_number="CORRECT-REF", issue_date="2026-08-18", confidence=0.98,
            ),
            hints=detect_context_hints("synthetic source text"),
            version="gemini:gemini-3.5-flash-lite:context-v3",
        )
        captured = {}
        with patch(
            "letter_registry.supabase_repository.build_supabase_context_processing_patch",
            side_effect=lambda record, *, owner_id, result: (captured.__setitem__("result", result) or {}),
        ), patch(
            "letter_registry.supabase_repository.build_supabase_letter_context_patch",
            return_value={"id": LETTER_ID, "owner_id": OWNER_ID},
        ):
            repository.save_context_result(record(), owner_id=OWNER_ID, result=result)

        saved = captured["result"].context
        self.assertEqual(saved.title, "Corrected source title")
        self.assertEqual(saved.reference_number, "CORRECT-REF")
        self.assertEqual(saved.issue_date, "2026-08-18")

    def test_human_reviewed_metadata_is_preserved_across_provider_migration(self) -> None:
        from unittest.mock import patch
        from letter_registry.context_hints import detect_context_hints
        from letter_registry.structured_analysis import ContextAnalysisResult, StructuredDocumentContext

        class ReviewedTransport(FakeTransport):
            def select(self, table, *, filters=None, columns="*"):
                if table == "letters":
                    return [{
                        "title": "Reviewed title", "authority": "Reviewed authority",
                        "category": "Reviewed category", "subcategory": None,
                        "summary": "Reviewed summary", "reference_number": "REVIEWED-REF",
                        "issue_date": "2025-06-02", "action_required": None,
                    }]
                if table == "letter_processing":
                    return [{
                        "structured_context": {"confidence": 0.8, "summary_hi": "समीक्षित सारांश"},
                        "context_version": "supabase-gemini:gemini-3.5-flash-lite:document-v3",
                        "reviewed_at": "2026-10-15T12:00:00Z",
                    }]
                return []

        transport = ReviewedTransport()
        repository = SupabaseLetterRepository(transport)
        result = ContextAnalysisResult(
            context=StructuredDocumentContext(
                title="Unreviewed new title", authority="New authority",
                category="New category", summary="New summary",
                reference_number="NEW-REF", issue_date="2026-08-18",
                summary_hi="नया सारांश", confidence=0.98,
            ),
            hints=detect_context_hints("synthetic source text"),
            version="gemini:gemini-3.5-flash-lite:context-v3",
        )
        captured = {}
        with patch(
            "letter_registry.supabase_repository.build_supabase_context_processing_patch",
            side_effect=lambda record, *, owner_id, result: (captured.__setitem__("result", result) or {}),
        ), patch(
            "letter_registry.supabase_repository.build_supabase_letter_context_patch",
            return_value={"id": LETTER_ID, "owner_id": OWNER_ID},
        ):
            repository.save_context_result(record(), owner_id=OWNER_ID, result=result)

        saved = captured["result"].context
        self.assertEqual(saved.title, "Reviewed title")
        self.assertEqual(saved.reference_number, "REVIEWED-REF")
        self.assertEqual(saved.issue_date, "2025-06-02")

    def test_low_confidence_direct_gemini_does_not_replace_stronger_metadata(self) -> None:
        from unittest.mock import patch
        from letter_registry.context_hints import detect_context_hints
        from letter_registry.structured_analysis import ContextAnalysisResult, StructuredDocumentContext

        class ExistingTransport(FakeTransport):
            def select(self, table, *, filters=None, columns="*"):
                if table == "letters":
                    return [{
                        "title": "Existing title", "authority": "Existing authority",
                        "category": "Existing category", "subcategory": None,
                        "summary": "Existing summary", "reference_number": "EXISTING-REF",
                        "issue_date": "2025-06-02", "action_required": "Existing action",
                    }]
                if table == "letter_processing":
                    return [{
                        "structured_context": {"confidence": 1.0, "summary_hi": "पुराना सारांश"},
                        "context_version": "supabase-gemini:gemini-3.5-flash-lite:document-v3",
                        "reviewed_at": None,
                    }]
                return []

        repository = SupabaseLetterRepository(ExistingTransport())
        result = ContextAnalysisResult(
            context=StructuredDocumentContext(
                title="Uncertain new title", authority="Uncertain authority",
                category="Uncertain category", summary="Uncertain summary",
                reference_number="UNCERTAIN-REF", issue_date="2026-08-18",
                confidence=0.45, needs_reprocessing=True,
            ),
            hints=detect_context_hints("synthetic source text"),
            version="gemini:gemini-3.5-flash-lite:context-v3",
        )
        captured = {}
        with patch(
            "letter_registry.supabase_repository.build_supabase_context_processing_patch",
            side_effect=lambda record, *, owner_id, result: (captured.__setitem__("result", result) or {}),
        ), patch(
            "letter_registry.supabase_repository.build_supabase_letter_context_patch",
            return_value={"id": LETTER_ID, "owner_id": OWNER_ID},
        ):
            repository.save_context_result(record(), owner_id=OWNER_ID, result=result)

        saved = captured["result"].context
        self.assertEqual(saved.title, "Existing title")
        self.assertEqual(saved.summary, "Existing summary")
        self.assertEqual(saved.confidence, 1.0)
        self.assertTrue(saved.needs_reprocessing)

    def test_low_confidence_source_conflict_replaces_stale_ai_metadata(self) -> None:
        from unittest.mock import patch
        from letter_registry.context_hints import detect_context_hints
        from letter_registry.structured_analysis import ContextAnalysisResult, StructuredDocumentContext

        class ExistingTransport(FakeTransport):
            def select(self, table, *, filters=None, columns="*"):
                if table == "letters":
                    return [{
                        "title": "Stale title", "authority": "Stale authority",
                        "category": "Stale category", "subcategory": None,
                        "summary": "Stale summary", "reference_number": "STALE-REF",
                        "issue_date": "2025-06-02", "action_required": "Stale action",
                    }]
                if table == "letter_processing":
                    return [{
                        "structured_context": {"confidence": 1.0},
                        "context_version": "supabase-gemini:gemini-3.5-flash-lite:document-v3",
                        "reviewed_at": None,
                    }]
                return []

        repository = SupabaseLetterRepository(ExistingTransport())
        result = ContextAnalysisResult(
            context=StructuredDocumentContext(
                title="Subject/body conflict", authority="Uncertain authority",
                category="teacher service", summary="Source conflict: subject and body disagree.",
                reference_number="UNCERTAIN-REF", issue_date="2026-08-18",
                confidence=0.45, needs_reprocessing=True,
                quality_flags=("source_content_conflict",),
            ),
            hints=detect_context_hints("synthetic source text"),
            version="gemini:gemini-3.5-flash-lite:context-v3",
        )
        captured = {}
        with patch(
            "letter_registry.supabase_repository.build_supabase_context_processing_patch",
            side_effect=lambda record, *, owner_id, result: (captured.__setitem__("result", result) or {}),
        ), patch(
            "letter_registry.supabase_repository.build_supabase_letter_context_patch",
            return_value={"id": LETTER_ID, "owner_id": OWNER_ID},
        ):
            repository.save_context_result(record(), owner_id=OWNER_ID, result=result)

        saved = captured["result"].context
        self.assertEqual(saved.summary, "Source conflict: subject and body disagree.")
        self.assertEqual(saved.title, "Subject/body conflict")
        self.assertEqual(saved.confidence, 0.45)
        self.assertTrue(saved.needs_reprocessing)

    def test_adapter_contains_no_runtime_credentials(self) -> None:
        transport = FakeTransport()
        repository = SupabaseLetterRepository(transport)

        self.assertFalse(hasattr(repository, "url"))
        self.assertFalse(hasattr(repository, "api_key"))
        self.assertFalse(hasattr(repository, "access_token"))


if __name__ == "__main__":
    unittest.main()
