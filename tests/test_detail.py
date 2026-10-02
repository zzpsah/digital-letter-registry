import unittest

from letter_registry.detail import SupabaseLetterDetailRepository


class FakeTransport:
    def select(self, table, *, filters=None, columns="*"):
        if table == "letters":
            return [{
                "id": "22222222-2222-4222-8222-222222222222",
                "smart_filename": "synthetic.pdf",
                "title": "Synthetic Letter",
                "authority": "Education Department",
                "category": "exam",
                "subcategory": "form",
                "issue_date": "2026-10-02",
                "status": "current",
                "action_required": "Review",
                "deadline_at": None,
            }]
        return [{
            "concepts": ["exam_form"],
            "structured_context": {"summary": "Synthetic summary"},
        }]


class DetailRepositoryTests(unittest.TestCase):
    def test_detail_excludes_private_storage_reference(self):
        detail = SupabaseLetterDetailRepository(FakeTransport()).get(
            "22222222-2222-4222-8222-222222222222"
        )

        self.assertIsNotNone(detail)
        self.assertEqual(detail.title, "Synthetic Letter")
        self.assertEqual(detail.structured_context["summary"], "Synthetic summary")
        self.assertFalse(hasattr(detail, "storage_object_id"))


if __name__ == "__main__":
    unittest.main()
