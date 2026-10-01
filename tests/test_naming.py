from datetime import date
import unittest

from letter_registry.naming import build_smart_filename


class SmartFilenameTests(unittest.TestCase):
    def test_filename_is_normalised_and_deterministic(self) -> None:
        filename = build_smart_filename(
            issue_date=date(2026, 9, 18),
            category="BSEB Examination",
            subject="Intermediate Exam Form Extension",
            original_filename="DOC10086.PDF",
            record_suffix="ltr_01",
        )

        self.assertEqual(
            filename,
            "2026-09-18_bseb-examination_intermediate-exam-form-extension_ltr-01.pdf",
        )

    def test_unknown_date_is_explicit(self) -> None:
        filename = build_smart_filename(
            issue_date=None,
            category="UDISE",
            subject="PEN Correction",
            original_filename="scan.jpg",
        )

        self.assertEqual(filename, "undated_udise_pen-correction.jpg")
