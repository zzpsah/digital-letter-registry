import unittest

from letter_registry.search import SupabaseSearchRepository


class FakeSearchTransport:
    def __init__(self) -> None:
        self.calls = []

    def rpc(self, function, params):
        self.calls.append((function, params))
        return [
            {
                "id": "22222222-2222-4222-8222-222222222222",
                "smart_filename": "inter-exam-extension__bseb__2026-10-01__REF-1.pdf",
                "title": "Inter Exam Form Extension",
                "authority": "BSEB",
                "category": "exam",
                "issue_date": "2026-10-01",
                "status": "current",
                "action_required": "Complete form before deadline",
                "concepts": ["exam_form", "deadline_extension"],
                "context_snippet": "इंटरमीडिएट परीक्षा प्रपत्र की अंतिम तिथि...",
                "text_rank": 0.8,
                "fuzzy_rank": 0.4,
                "combined_rank": 0.7,
            }
        ]


class SearchRepositoryTests(unittest.TestCase):
    def test_query_is_normalized_and_rpc_is_used(self) -> None:
        transport = FakeSearchTransport()
        repository = SupabaseSearchRepository(transport)

        results = repository.search("  inter   exam   last date  ", limit=10)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].authority, "BSEB")
        self.assertIn("deadline_extension", results[0].concepts)
        self.assertEqual(
            transport.calls[0],
            (
                "search_letters",
                {"search_query": "inter exam last date", "result_limit": 10},
            ),
        )

    def test_blank_query_returns_no_results_without_rpc(self) -> None:
        transport = FakeSearchTransport()
        repository = SupabaseSearchRepository(transport)

        self.assertEqual(repository.search("   "), [])
        self.assertEqual(transport.calls, [])

    def test_limit_is_bounded(self) -> None:
        repository = SupabaseSearchRepository(FakeSearchTransport())
        with self.assertRaises(ValueError):
            repository.search("udise", limit=101)


if __name__ == "__main__":
    unittest.main()
