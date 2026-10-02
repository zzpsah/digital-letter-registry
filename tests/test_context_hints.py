import unittest

from letter_registry.context_hints import detect_context_hints


class ContextHintsTests(unittest.TestCase):
    def test_hindi_government_letter_concepts(self) -> None:
        text = """
        बिहार विद्यालय परीक्षा समिति
        विषय: इंटरमीडिएट परीक्षा प्रपत्र भरने की अंतिम तिथि के संबंध में
        पूर्व निर्धारित अंतिम तिथि में अवधि विस्तार किया जाता है।
        आवश्यक कार्रवाई सुनिश्चित करें।
        """

        hints = detect_context_hints(text)

        self.assertIn("intermediate", hints.concepts)
        self.assertIn("exam_form", hints.concepts)
        self.assertIn("deadline", hints.concepts)
        self.assertIn("deadline_extension", hints.concepts)
        self.assertIn("required_action", hints.concepts)

    def test_udise_pen_correction_concepts(self) -> None:
        hints = detect_context_hints(
            "UDISE+ में PEN correction एवं student verification के संबंध में निर्देश"
        )

        self.assertIn("udise", hints.concepts)
        self.assertIn("pen", hints.concepts)
        self.assertIn("correction", hints.concepts)
        self.assertIn("verification", hints.concepts)

    def test_structure_markers_are_separate_from_concepts(self) -> None:
        hints = detect_context_hints(
            "पत्रांक 123 दिनांक 01-10-2026 विषय छात्रवृत्ति आवेदन"
        )

        self.assertIn("scholarship", hints.concepts)
        self.assertIn("पत्रांक", hints.structure_terms)
        self.assertIn("दिनांक", hints.structure_terms)
        self.assertIn("विषय", hints.structure_terms)


if __name__ == "__main__":
    unittest.main()
