import unittest

from letter_registry.reprocessing import (
    ReprocessingTargets,
    SupabaseReprocessingPlanner,
)


class FakeTransport:
    def select(self, table, *, filters=None, columns="*"):
        return [
            {
                "letter_id": "11111111-1111-4111-8111-111111111111",
                "ocr_version": "ocr-v1",
                "context_version": "context-v1",
                "dictionary_version": "dict-v1",
                "filename_rule_version": "name-v1",
                "category_schema_version": "cat-v1",
                "embedding_version": "embed-v1",
                "status_rule_version": "status-v1",
            },
            {
                "letter_id": "22222222-2222-4222-8222-222222222222",
                "ocr_version": "ocr-v2",
                "context_version": "context-v2",
                "dictionary_version": "dict-v2",
                "filename_rule_version": "name-v2",
                "category_schema_version": "cat-v2",
                "embedding_version": "embed-v2",
                "status_rule_version": "status-v2",
            },
        ]


class ReprocessingPlannerTests(unittest.TestCase):
    def test_preview_returns_only_version_mismatches(self):
        targets = ReprocessingTargets(
            ocr_version="ocr-v2",
            context_version="context-v2",
            dictionary_version="dict-v2",
            filename_rule_version="name-v2",
            category_schema_version="cat-v2",
            embedding_version="embed-v2",
            status_rule_version="status-v2",
        )
        rows = SupabaseReprocessingPlanner(FakeTransport()).preview(targets)

        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows[0].letter_id,
            "11111111-1111-4111-8111-111111111111",
        )
        self.assertIn("embedding_version", rows[0].reasons)
        self.assertEqual(rows[0].target_versions["ocr_version"], "ocr-v2")

    def test_all_target_versions_are_required(self):
        with self.assertRaises(ValueError):
            ReprocessingTargets(
                ocr_version="",
                context_version="context-v2",
                dictionary_version="dict-v2",
                filename_rule_version="name-v2",
                category_schema_version="cat-v2",
                embedding_version="embed-v2",
                status_rule_version="status-v2",
            )


if __name__ == "__main__":
    unittest.main()
