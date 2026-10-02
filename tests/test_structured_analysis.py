import unittest

from letter_registry.structured_analysis import (
    StructuredDocumentContext,
    analyze_document_context,
)


class FakeProvider:
    version = "fake-context-v1"

    def analyze(self, *, extracted_text, hints):
        return StructuredDocumentContext(
            title="Intermediate Exam Form Date Extension",
            authority="BSEB",
            category="exam",
            summary="Synthetic structured summary",
            action_required="Complete exam form before extended deadline",
            concepts=("exam_form",),
            related_terms_hi=("परीक्षा प्रपत्र", "अंतिम तिथि"),
            related_terms_en=("exam form", "deadline extension"),
            confidence=0.9,
        )


class StructuredAnalysisTests(unittest.TestCase):
    def test_deterministic_hints_merge_with_provider_concepts(self) -> None:
        result = analyze_document_context(
            "इंटरमीडिएट परीक्षा प्रपत्र की अंतिम तिथि में अवधि विस्तार किया गया है।",
            provider=FakeProvider(),
        )

        self.assertEqual(result.version, "fake-context-v1")
        self.assertIn("exam_form", result.context.concepts)
        self.assertIn("deadline", result.context.concepts)
        self.assertIn("deadline_extension", result.context.concepts)
        self.assertEqual(result.context.authority, "BSEB")

    def test_context_serializes_to_public_safe_json_shape(self) -> None:
        context = StructuredDocumentContext(
            title="Synthetic",
            concepts=("udise", "pen"),
        )
        data = context.to_json_dict()

        self.assertEqual(data["title"], "Synthetic")
        self.assertEqual(data["concepts"], ["udise", "pen"])


if __name__ == "__main__":
    unittest.main()
