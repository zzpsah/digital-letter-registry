import unittest

from letter_registry.search import SearchFilters, SupabaseSearchRepository


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
                "file_type": "pdf",
                "text_rank": 0.8,
                "fuzzy_rank": 0.4,
                "combined_rank": 0.7,
            }
        ]


class SearchRepositoryTests(unittest.TestCase):
    def test_query_and_filters_are_normalized_and_rpc_is_used(self) -> None:
        transport = FakeSearchTransport()
        repository = SupabaseSearchRepository(transport)

        results = repository.search(
            "  inter   exam   last date  ",
            filters=SearchFilters(
                authority="BSEB",
                status="current",
                year=2026,
                file_type="pdf",
            ),
            limit=10,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].authority, "BSEB")
        self.assertEqual(results[0].file_type, "pdf")
        self.assertIn("deadline_extension", results[0].concepts)
        self.assertEqual(transport.calls[0][0], "search_letter_cards")
        self.assertEqual(
            transport.calls[0][1],
            {
                "search_query": "inter exam last date",
                "authority_filter": "BSEB",
                "category_filter": None,
                "status_filter": "current",
                "year_filter": 2026,
                "file_type_filter": "pdf",
                "result_limit": 10,
            },
        )

    def test_blank_query_can_still_use_filters(self) -> None:
        transport = FakeSearchTransport()
        repository = SupabaseSearchRepository(transport)

        results = repository.search("", filters=SearchFilters(category="udise"))

        self.assertEqual(len(results), 1)
        self.assertIsNone(transport.calls[0][1]["search_query"])
        self.assertEqual(transport.calls[0][1]["category_filter"], "udise")

    def test_limit_is_bounded(self) -> None:
        repository = SupabaseSearchRepository(FakeSearchTransport())
        with self.assertRaises(ValueError):
            repository.search("udise", limit=101)

    def test_year_is_bounded(self) -> None:
        repository = SupabaseSearchRepository(FakeSearchTransport())
        with self.assertRaises(ValueError):
            repository.search("", filters=SearchFilters(year=1800))


if __name__ == "__main__":
    unittest.main()
