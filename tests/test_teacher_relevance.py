import unittest

from letter_registry.teacher_relevance import (
    AUTO_COMMENT_PREFIX,
    classify_computer_science_teacher_letter,
    merge_auto_comment,
)


class ComputerScienceTeacherRelevanceTests(unittest.TestCase):
    def test_explicit_computer_science_teacher_phrase_matches(self):
        result = classify_computer_science_teacher_letter(
            extracted_text="The service rules for Computer Science Teachers are clarified.",
            title="Teacher service clarification",
        )
        self.assertTrue(result.is_relevant)
        self.assertIn("Computer Science Teacher", result.evidence)
        self.assertIn(AUTO_COMMENT_PREFIX, result.comment or "")

    def test_hindi_computer_teacher_phrase_matches(self):
        result = classify_computer_science_teacher_letter(
            extracted_text="कंप्यूटर विज्ञान शिक्षकों की नियुक्ति एवं वरीयता के संबंध में।"
        )
        self.assertTrue(result.is_relevant)

    def test_subject_plus_service_context_matches(self):
        result = classify_computer_science_teacher_letter(
            extracted_text="Computer Science subject teachers' seniority and pay scale rules."
        )
        self.assertTrue(result.is_relevant)

    def test_generic_computer_mention_does_not_match(self):
        result = classify_computer_science_teacher_letter(
            extracted_text="All schools must repair computer equipment in the ICT lab."
        )
        self.assertFalse(result.is_relevant)

    def test_teacher_letter_without_computer_science_does_not_match(self):
        result = classify_computer_science_teacher_letter(
            extracted_text="General teacher transfer and seniority instructions."
        )
        self.assertFalse(result.is_relevant)

    def test_auto_comment_replaces_prior_auto_note_and_preserves_human_note(self):
        existing = "Please check this order.\n\n[Auto-CS relevance] Old generated note."
        merged = merge_auto_comment(existing, "[Auto-CS relevance] New generated note.")
        self.assertIn("Please check this order.", merged)
        self.assertIn("New generated note.", merged)
        self.assertNotIn("Old generated note.", merged)


if __name__ == "__main__":
    unittest.main()
