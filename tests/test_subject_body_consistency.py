import unittest

from letter_registry.subject_body_consistency import detect_subject_body_conflict


class SubjectBodyConsistencyTests(unittest.TestCase):
    def test_arrears_subject_with_leave_body_is_flagged(self):
        text = (
            "विषय :- राज्य के विद्यालय अध्यापकों के बकाया की स्वीकृति के संबंध में।\n"
            "प्रसंगः- ज्ञापांक-444, दिनांक-02.06.2025\n"
            "महोदय,\n"
            "शिक्षकों के अवकाश की स्वीकृति के संबंध में निर्देश। ई-शिक्षाकोष Leave Module "
            "से leave applications ऑनलाइन जमा और स्वीकृत किए जाएँ।\n"
        )
        conflict = detect_subject_body_conflict(text)
        self.assertIsNotNone(conflict)
        self.assertEqual(conflict.subject_topic, "arrears approval")
        self.assertEqual(conflict.body_topic, "leave approval")

    def test_consistent_leave_subject_and_body_is_not_flagged(self):
        text = (
            "विषय :- शिक्षकों के अवकाश की स्वीकृति के संबंध में।\n"
            "प्रसंगः- पूर्व निर्देश\n"
            "महोदय,\n"
            "ई-शिक्षाकोष Leave Module के माध्यम से अवकाश आवेदन ऑनलाइन जमा करें।\n"
        )
        self.assertIsNone(detect_subject_body_conflict(text))

    def test_missing_subject_heading_is_not_guessed(self):
        self.assertIsNone(detect_subject_body_conflict("महोदय, अवकाश आवेदन ऑनलाइन जमा करें।"))


if __name__ == "__main__":
    unittest.main()
