import unittest

from letter_registry.models import DocumentRelationship
from letter_registry.relationships import (
    RelationshipReviewStatus,
    RelationshipSuggestion,
    SupabaseRelationshipRepository,
)


class FakeTransport:
    def __init__(self):
        self.rows = []
        self.rpc_calls = []

    def upsert(self, table, row, *, on_conflict):
        self.rows.append((table, row, on_conflict))
        return {"id": "44444444-4444-4444-8444-444444444444"}

    def select(self, table, *, filters=None, columns="*"):
        if filters and "source_letter_id" in filters:
            return [{
                "id": "44444444-4444-4444-8444-444444444444",
                "source_letter_id": filters["source_letter_id"],
                "target_letter_id": "22222222-2222-4222-8222-222222222222",
                "relationship_type": "supersedes",
                "confidence": 0.95,
                "review_status": "suggested",
                "relationship_version": "rules-v1",
                "rationale": "Synthetic",
                "reviewed_at": None,
            }]
        return []

    def rpc(self, function, params):
        self.rpc_calls.append((function, params))
        if function == "review_letter_relationship":
            return [{"success": True}]
        return [{"updated_superseded": 1, "updated_current": 0}]


class RelationshipTests(unittest.TestCase):
    def test_suggestion_is_stored_as_reviewable(self):
        transport = FakeTransport()
        repo = SupabaseRelationshipRepository(transport)
        repo.save_suggestion(
            RelationshipSuggestion(
                source_letter_id="11111111-1111-4111-8111-111111111111",
                target_letter_id="22222222-2222-4222-8222-222222222222",
                relationship_type=DocumentRelationship.SUPERSEDES,
                confidence=0.95,
                rationale="Synthetic extension chain",
                version="rules-v1",
            ),
            owner_id="33333333-3333-4333-8333-333333333333",
        )
        row = transport.rows[0][1]
        self.assertEqual(row["review_status"], "suggested")
        self.assertEqual(row["relationship_version"], "rules-v1")

    def test_review_uses_explicit_rpc(self):
        transport = FakeTransport()
        repo = SupabaseRelationshipRepository(transport)
        ok = repo.review(
            "44444444-4444-4444-8444-444444444444",
            decision=RelationshipReviewStatus.CONFIRMED,
        )
        self.assertTrue(ok)
        self.assertEqual(
            transport.rpc_calls[0][0],
            "review_letter_relationship",
        )

    def test_suggested_is_not_a_review_decision(self):
        repo = SupabaseRelationshipRepository(FakeTransport())
        with self.assertRaises(ValueError):
            repo.review(
                "44444444-4444-4444-8444-444444444444",
                decision=RelationshipReviewStatus.SUGGESTED,
            )

    def test_list_for_letter_returns_review_state(self):
        repo = SupabaseRelationshipRepository(FakeTransport())
        rows = repo.list_for_letter(
            "11111111-1111-4111-8111-111111111111"
        )
        self.assertEqual(rows[0]["review_status"], "suggested")


if __name__ == "__main__":
    unittest.main()
