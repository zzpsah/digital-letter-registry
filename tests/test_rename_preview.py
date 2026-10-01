from datetime import date
import unittest

from letter_registry.rename_preview import RenameCandidate, build_rename_preview


class RenamePreviewTests(unittest.TestCase):
    def test_preview_returns_mapping_without_provider_side_effects(self) -> None:
        candidates = [
            RenameCandidate(
                original_filename="DOC10086.pdf",
                short_title="Scholarship Guidelines",
                issuer="Education Department",
                issue_date=date(2026, 10, 1),
                reference_number="REF-001",
            ),
            RenameCandidate(
                original_filename="scan.jpg",
                short_title="परीक्षा फॉर्म तिथि विस्तार",
                issuer="शिक्षा विभाग",
            ),
        ]

        previews = build_rename_preview(candidates)

        self.assertEqual(len(previews), 2)
        self.assertEqual(previews[0].original_filename, "DOC10086.pdf")
        self.assertEqual(
            previews[0].proposed_filename,
            "scholarship-guidelines__education-department__2026-10-01__REF-001.pdf",
        )
        self.assertEqual(
            previews[1].proposed_filename,
            "परीक्षा-फॉर्म-तिथि-विस्तार__शिक्षा-विभाग__undated__no-ref.jpg",
        )
        self.assertTrue(all(item.changed for item in previews))


if __name__ == "__main__":
    unittest.main()
