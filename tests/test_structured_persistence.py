from datetime import datetime, timezone
import unittest

from letter_registry.models import DocumentRecord
from letter_registry.persistence import (
    build_supabase_context_processing_patch,
    build_supabase_letter_context_patch,
)
from letter_registry.structured_analysis import (
    ContextAnalysisResult,
    StructuredDocumentContext,
)
from letter_registry.context_hints import ContextHints


class StructuredContextPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.record = DocumentRecord(
            record_id="22222222-2222-4222-8222-222222222222",
            original_filename="synthetic.pdf",
            original_sha256="a" * 64,
            original_storage_reference="synthetic-reference",
            received_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
        )
        self.result = ContextAnalysisResult(
            context=StructuredDocumentContext(
                title="UDISE PEN Correction Instructions",
                authority="Education Department",
                category="udise",
                subcategory="pen-correction",
                summary="Synthetic summary",
                action_required="Verify PEN data",
                concepts=("udise", "pen", "correction"),
                deadline="2026-10-10T23:59:59+05:30",
                confidence=0.91,
            ),
            hints=ContextHints(
                concepts=("udise", "pen"),
                matched_terms=("UDISE", "PEN"),
                structure_terms=(),
            ),
            version="fake-context-v1",
        )

    def test_processing_patch_contains_context_json_and_version(self) -> None:
        row = build_supabase_context_processing_patch(
            self.record,
            owner_id="11111111-1111-4111-8111-111111111111",
            result=self.result,
        )

        self.assertEqual(row["context_version"], "fake-context-v1")
        self.assertEqual(row["concepts"], ["udise", "pen", "correction"])
        self.assertEqual(
            row["structured_context"]["action_required"],
            "Verify PEN data",
        )

    def test_letter_patch_contains_searchable_metadata(self) -> None:
        row = build_supabase_letter_context_patch(
            self.record,
            owner_id="11111111-1111-4111-8111-111111111111",
            result=self.result,
        )

        self.assertEqual(row["title"], "UDISE PEN Correction Instructions")
        self.assertEqual(row["authority"], "Education Department")
        self.assertEqual(row["category"], "udise")
        self.assertEqual(row["deadline_at"], "2026-10-10T23:59:59+05:30")


if __name__ == "__main__":
    unittest.main()
