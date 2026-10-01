from datetime import date
import unittest

from letter_registry.rename_preview import (
    RenameCandidate,
    build_rename_preview,
    render_rename_preview_csv,
)


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

    def test_csv_report_is_reviewable_and_contains_no_provider_logic(self) -> None:
        previews = build_rename_preview(
            [
                RenameCandidate(
                    original_filename="scan.pdf",
                    short_title="Inter Exam Schedule",
                    issuer="Education Department",
                )
            ]
        )

        report = render_rename_preview_csv(previews)

        self.assertIn("original_filename,proposed_filename,changed", report)
        self.assertIn("scan.pdf", report)
        self.assertIn(
            "inter-exam-schedule__education-department__undated__no-ref.pdf",
            report,
        )
        self.assertIn(",yes", report)


if __name__ == "__main__":
    unittest.main()
