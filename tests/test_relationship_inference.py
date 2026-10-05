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


    def test_same_reference_high_similarity_suggests_duplicate(self):
        rows = infer_relationship_suggestions(
            source_letter_id="11111111-1111-4111-8111-111111111111",
            source_reference_number="BSEB/123/2026",
            source_authority="BSEB",
            source_category="exam",
            source_text="सामान्य सूचना",
            source_title="Exam Form Notice",
            source_summary="Original notice",
            candidates=[self.candidate],
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].relationship_type, DocumentRelationship.DUPLICATE_OF)
        self.assertGreater(rows[0].confidence, 0.9)

    def test_same_reference_material_difference_suggests_related_version(self):
        rows = infer_relationship_suggestions(
            source_letter_id="11111111-1111-4111-8111-111111111111",
            source_reference_number="BSEB/123/2026",
            source_authority="BSEB",
            source_category="exam",
            source_text="सामान्य सूचना",
            source_title="Completely Changed Fee Direction",
            source_summary="Different operational instructions and changed conditions",
            candidates=[self.candidate],
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].relationship_type, DocumentRelationship.RELATED_TO)
        self.assertIn("Possible revised/versioned document", rows[0].rationale)

    def test_newer_revised_same_reference_recommends_supersede(self):
        candidate = RelationshipCandidate(
            record_id="33333333-3333-4333-8333-333333333333",
            reference_number="BSEB/777/2026",
            authority="BSEB",
            category="fee",
            title="School Fee Order",
            summary="School fee rates and collection rules",
            issue_date="2026-09-01",
        )
        rows = infer_relationship_suggestions(
            source_letter_id="11111111-1111-4111-8111-111111111111",
            source_reference_number="BSEB/777/2026",
            source_authority="BSEB",
            source_category="fee",
            source_text="Revised school fee rates and collection rules are issued.",
            source_title="Revised School Fee Order",
            source_summary="Revised school fee rates and collection rules",
            source_issue_date="2026-10-01",
            candidates=[candidate],
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].relationship_type, DocumentRelationship.SUPERSEDES)
        self.assertGreater(rows[0].confidence, 0.9)


    def test_no_reference_requires_very_high_metadata_similarity(self):
        candidate = RelationshipCandidate(
            record_id="33333333-3333-4333-8333-333333333333",
            reference_number=None,
            authority="District Education Officer Siwan",
            category="attendance",
            title="eShikshaKosh Attendance Notice for Schools",
            summary="Schools must ensure eShikshaKosh attendance compliance and review records daily.",
        )
        rows = infer_relationship_suggestions(
            source_letter_id="11111111-1111-4111-8111-111111111111",
            source_reference_number=None,
            source_authority="District Education Officer Siwan",
            source_category="attendance",
            source_text="notice",
            source_title="eShikshaKosh Attendance Notice for Schools",
            source_summary="Schools must ensure eShikshaKosh attendance compliance and review records daily.",
            candidates=[candidate],
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].relationship_type, DocumentRelationship.DUPLICATE_OF)



if __name__ == "__main__":
    unittest.main()
