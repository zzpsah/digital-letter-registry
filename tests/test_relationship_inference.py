import unittest

from letter_registry.models import DocumentRelationship
from letter_registry.relationship_inference import (
    RelationshipCandidate,
    infer_relationship_suggestions,
)


class RelationshipInferenceTests(unittest.TestCase):
    def setUp(self):
        self.candidate = RelationshipCandidate(
            record_id="22222222-2222-4222-8222-222222222222",
            reference_number="BSEB/123/2026",
            authority="BSEB",
            category="exam",
            title="Exam Form Notice",
            summary="Original notice",
        )

    def test_extension_requires_explicit_cue_and_reference(self):
        rows = infer_relationship_suggestions(
            source_letter_id="11111111-1111-4111-8111-111111111111",
            source_reference_number="BSEB/456/2026",
            source_authority="BSEB",
            source_category="exam",
            source_text=(
                "BSEB/123/2026 के संदर्भ में परीक्षा प्रपत्र की "
                "अंतिम तिथि हेतु तिथि विस्तार किया जाता है।"
            ),
            candidates=[self.candidate],
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows[0].relationship_type,
            DocumentRelationship.EXTENDS,
        )
        self.assertGreater(rows[0].confidence, 0.9)

    def test_reference_without_relationship_wording_is_not_enough(self):
        rows = infer_relationship_suggestions(
            source_letter_id="11111111-1111-4111-8111-111111111111",
            source_reference_number=None,
            source_authority="BSEB",
            source_category="exam",
            source_text="संदर्भ BSEB/123/2026 के अनुसार अनुपालन करें।",
            candidates=[self.candidate],
        )
        self.assertEqual(rows, [])

    def test_explicit_cue_without_reference_match_is_not_enough(self):
        rows = infer_relationship_suggestions(
            source_letter_id="11111111-1111-4111-8111-111111111111",
            source_reference_number=None,
            source_authority="BSEB",
            source_category="exam",
            source_text="परीक्षा की अंतिम तिथि में तिथि विस्तार किया जाता है।",
            candidates=[self.candidate],
        )
        self.assertEqual(rows, [])

    def test_correction_cue_maps_to_corrects(self):
        rows = infer_relationship_suggestions(
            source_letter_id="11111111-1111-4111-8111-111111111111",
            source_reference_number=None,
            source_authority="BSEB",
            source_category="exam",
            source_text="BSEB/123/2026 के संबंध में यह शुद्धि पत्र जारी है।",
            candidates=[self.candidate],
        )
        self.assertEqual(
            rows[0].relationship_type,
            DocumentRelationship.CORRECTS,
        )


if __name__ == "__main__":
    unittest.main()
