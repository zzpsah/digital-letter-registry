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

    def test_incidental_computer_teacher_mention_in_unrelated_circular_does_not_match(self):
        result = classify_computer_science_teacher_letter(
            title="Sports competition and expenditure guidelines",
            summary="Instructions for organising the annual sports competition.",
            extracted_text="कंप्यूटर शिक्षक को कार्यक्रम में उपस्थित रहने हेतु कहा गया है। खेल प्रतियोगिता के व्यय का विवरण दें।",
        )
        self.assertFalse(result.is_relevant)

    def test_sports_circular_is_not_marked_for_incidental_teacher_mention(self):
        result = classify_computer_science_teacher_letter(
            title="मशाल-2024 खेल प्रतियोगिता के आयोजन एवं व्यय संबंधी दिशा-निर्देश",
            summary="Guidelines for sports competition, player training and expenditure.",
            action_required="Ensure timely organisation of sports events and expenditure reporting.",
            extracted_text="कंप्यूटर शिक्षक का नाम विद्यालय समिति की सूची में है।",
        )
        self.assertFalse(result.is_relevant)

    def test_computer_teacher_assignment_as_nodal_officer_matches(self):
        result = classify_computer_science_teacher_letter(
            extracted_text="कंप्यूटर विज्ञान शिक्षक को APAAR ID निर्माण के लिए नोडल अधिकारी नामित किया जाता है।"
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
