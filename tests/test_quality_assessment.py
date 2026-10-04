import unittest

from letter_registry.quality_assessment import assess_document_quality


class DocumentQualityAssessmentTests(unittest.TestCase):
    def test_high_quality_document_is_not_flagged(self):
        result = assess_document_quality(
            extracted_text=("जिला शिक्षा पदाधिकारी द्वारा विद्यालयों को उपस्थिति "
                            "सुनिश्चित करने हेतु निर्देश जारी किया गया है। " * 12),
            context_confidence=0.96,
            title="Attendance compliance instructions",
            authority="District Education Officer",
            category="attendance",
            reference_number="123/2026",
            issue_date="2026-10-04",
            clean_document_text="स्वच्छ हिंदी पाठ उपलब्ध है।",
        )
        self.assertGreaterEqual(result.score, 0.72)
        self.assertFalse(result.needs_reprocessing)

    def test_low_quality_document_is_flagged_without_blocking(self):
        result = assess_document_quality(
            extracted_text="||| � x _",
            context_confidence=0.42,
            title=None,
            authority=None,
            category=None,
            reference_number=None,
            issue_date=None,
            clean_document_text=None,
        )
        self.assertLess(result.score, 0.72)
        self.assertTrue(result.needs_reprocessing)
        self.assertIn("low_ocr_readability", result.flags)

    def test_missing_reference_date_alone_does_not_force_failure(self):
        result = assess_document_quality(
            extracted_text=("विद्यालय शिक्षा विभाग द्वारा नामांकन संबंधी महत्वपूर्ण सूचना "
                            "विद्यालयों को जारी की गई है। " * 10),
            context_confidence=0.94,
            title="Admission notice",
            authority="Education Department",
            category="admission",
            reference_number=None,
            issue_date=None,
            clean_document_text="नामांकन संबंधी स्वच्छ पाठ।",
        )
        self.assertTrue(result.score > 0.72)
        self.assertIn("missing_reference_and_date", result.flags)


    def test_qualitative_confidence_is_normalized(self):
        result = assess_document_quality(
            extracted_text=("विद्यालय उपस्थिति संबंधी स्पष्ट निर्देश " * 20),
            context_confidence="high",
            title="Attendance notice",
            authority="Education Department",
            category="attendance",
            reference_number="123/2026",
            issue_date="2026-10-04",
            clean_document_text="स्पष्ट हिंदी पाठ उपलब्ध है।",
        )
        self.assertFalse(result.needs_reprocessing)
        self.assertNotIn("missing_or_invalid_context_confidence", result.flags)

    def test_invalid_confidence_never_crashes(self):
        result = assess_document_quality(
            extracted_text="विद्यालय सूचना " * 10,
            context_confidence="unexpected-value",
            title="Notice",
            authority="Education Department",
            category="notice",
            reference_number=None,
            issue_date=None,
            clean_document_text=None,
        )
        self.assertIn("missing_or_invalid_context_confidence", result.flags)


if __name__ == "__main__":
    unittest.main()
