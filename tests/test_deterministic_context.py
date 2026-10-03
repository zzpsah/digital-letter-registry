import unittest

from letter_registry.context_hints import detect_context_hints
from letter_registry.deterministic_context import DeterministicDocumentContextProvider


class DeterministicContextTests(unittest.TestCase):
    def test_bseb_exam_extension_is_classified_conservatively(self):
        text = (
            "बिहार विद्यालय परीक्षा समिति द्वारा परीक्षा प्रपत्र की अंतिम तिथि "
            "में तिथि विस्तार किया गया है। आवश्यक कार्रवाई सुनिश्चित करें।"
        )
        hints = detect_context_hints(text)

        result = DeterministicDocumentContextProvider().analyze(
            extracted_text=text,
            hints=hints,
        )

        self.assertEqual(result.authority, "BSEB")
        self.assertEqual(result.category, "exam")
        self.assertEqual(result.title, "Exam Form Deadline Extension")
        self.assertIn("exam_form", result.concepts)
        self.assertIn("deadline_extension", result.concepts)
        self.assertIsNone(result.issue_date)
        self.assertIsNone(result.reference_number)
        self.assertIsNone(result.deadline)

    def test_unknown_text_does_not_invent_structured_facts(self):
        text = "यह एक सामान्य सिंथेटिक परीक्षण दस्तावेज है।"
        hints = detect_context_hints(text)

        result = DeterministicDocumentContextProvider().analyze(
            extracted_text=text,
            hints=hints,
        )

        self.assertIsNone(result.authority)
        self.assertIsNone(result.category)
        self.assertIsNone(result.title)
        self.assertIsNone(result.issue_date)
        self.assertIsNone(result.reference_number)
        self.assertIsNone(result.action_required)


if __name__ == "__main__":
    unittest.main()
