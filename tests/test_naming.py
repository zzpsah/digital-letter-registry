from datetime import date
import unittest

from letter_registry.naming import build_smart_filename


class SmartFilenameTests(unittest.TestCase):
    def test_english_filename_uses_official_pattern(self) -> None:
        filename = build_smart_filename(
            short_title="Scholarship Guidelines",
            issuer="Education Department",
            issue_date=date(2026, 10, 1),
            reference_number="REF-001",
            original_filename="DOC10086.pdf",
        )

        self.assertEqual(
            filename,
            "scholarship-guidelines__education-department__2026-10-01__REF-001.pdf",
        )

    def test_hindi_is_preserved(self) -> None:
        filename = build_smart_filename(
            short_title="छात्रवृत्ति निर्देश",
            issuer="शिक्षा विभाग",
            issue_date=date(2026, 10, 1),
            reference_number="REF-001",
            original_filename="scan.pdf",
        )

        self.assertEqual(
            filename,
            "छात्रवृत्ति-निर्देश__शिक्षा-विभाग__2026-10-01__REF-001.pdf",
        )

    def test_hinglish_and_punctuation_are_normalized(self) -> None:
        filename = build_smart_filename(
            short_title="Inter परीक्षा Form / Date Extension",
            issuer="BSEB - शिक्षा विभाग",
            issue_date=None,
            reference_number=None,
            original_filename="image.JPG",
        )

        self.assertEqual(
            filename,
            "inter-परीक्षा-form-date-extension__bseb-शिक्षा-विभाग__undated__no-ref.JPG",
        )

    def test_unknown_date_and_reference_use_placeholders(self) -> None:
        filename = build_smart_filename(
            short_title="Inter Exam Schedule",
            issuer="Education Department",
            issue_date=None,
            reference_number="",
            original_filename="letter.pdf",
        )

        self.assertEqual(
            filename,
            "inter-exam-schedule__education-department__undated__no-ref.pdf",
        )

    def test_original_extension_case_is_preserved(self) -> None:
        filename = build_smart_filename(
            short_title="UDISE PEN Correction",
            issuer="Education Department",
            issue_date=None,
            reference_number=None,
            original_filename="scan.PDF",
        )

        self.assertTrue(filename.endswith(".PDF"))

    def test_long_fields_keep_date_and_reference_segments(self) -> None:
        filename = build_smart_filename(
            short_title="A" * 200,
            issuer="B" * 120,
            issue_date=date(2026, 10, 1),
            reference_number="REF-" + ("9" * 80),
            original_filename="scan.pdf",
        )

        parts = filename[:-4].split("__")
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[2], "2026-10-01")
        self.assertTrue(parts[3].startswith("REF-"))
        self.assertLessEqual(len(filename), 220)

    def test_extension_is_required(self) -> None:
        with self.assertRaises(ValueError):
            build_smart_filename(
                short_title="Letter",
                issuer="Department",
                issue_date=None,
                reference_number=None,
                original_filename="no-extension",
            )


if __name__ == "__main__":
    unittest.main()
