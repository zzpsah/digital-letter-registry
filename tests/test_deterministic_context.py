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

    def test_transfer_order_extracts_explicit_structured_facts(self):
        text = (
            "कार्यालय जिला शिक्षा पदाधिकारी, SIWAN\n"
            "स्थानांतरण / पदस्थापन आदेश\n"
            "पत्रांक: SIWA/Transfer2.0/RT/2026/00736 दिनांक : 26/09/2026\n"
            "शिक्षक का नाम : SYNTHETIC PERSON\n"
            "जिला के अंदर स्थानांतरण हेतु आदेश निर्गत किया जाता है।"
        )
        hints = detect_context_hints(text)

        result = DeterministicDocumentContextProvider().analyze(
            extracted_text=text,
            hints=hints,
        )

        self.assertEqual(result.title, "स्थानांतरण / पदस्थापन आदेश")
        self.assertEqual(result.authority, "कार्यालय जिला शिक्षा पदाधिकारी, SIWAN")
        self.assertEqual(result.category, "transfer-posting")
        self.assertEqual(
            result.reference_number,
            "SIWA/Transfer2.0/RT/2026/00736",
        )
        self.assertEqual(result.issue_date, "2026-09-26")
        self.assertGreater(result.confidence or 0, 0.5)

    def test_cbse_affiliation_notification_wins_over_generic_udise_terms(self):
        text = (
            "CENTRAL BOARD OF SECONDARY EDUCATION\n"
            "CBSE/AFF./Notification/2026 Dated: 26/02/2026\n"
            "NOTIFICATION\n"
            "Subject: Submission of applications under various categories "
            "of affiliation for the session 2027-28 in SARAS 7.0.\n"
            "Schools should update UDISE information where required."
        )
        hints = detect_context_hints(text)

        result = DeterministicDocumentContextProvider().analyze(
            extracted_text=text,
            hints=hints,
        )

        self.assertEqual(result.authority, "CBSE")
        self.assertEqual(result.title, "CBSE Affiliation Notification")
        self.assertEqual(result.category, "affiliation")
        self.assertEqual(
            result.reference_number,
            "CBSE/AFF./Notification/2026",
        )
        self.assertEqual(result.issue_date, "2026-02-26")

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
