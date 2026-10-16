from __future__ import annotations

import copy
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from letter_registry.access import ArchiveMembership, ArchiveRole
from letter_registry.api import ApiDependencies, create_app


ADMIN_ID = "11111111-1111-4111-8111-111111111111"
FLAGGED_ID = "22222222-2222-4222-8222-222222222222"
REVIEWED_ID = "33333333-3333-4333-8333-333333333333"
NORMAL_ID = "44444444-4444-4444-8444-444444444444"
ARCHIVE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


class FakeReviewDatabase:
    def __init__(self) -> None:
        self.processing = [
            {
                "letter_id": FLAGGED_ID,
                "structured_context": {
                    "title": "Synthetic review document",
                    "summary": "Synthetic summary",
                    "authority": "Synthetic authority",
                    "category": "notice",
                    "confidence": 0.45,
                    "needs_reprocessing": True,
                    "quality_flags": ["source_content_conflict", "missing_reference_and_date"],
                    "clean_document_text": "MUST NOT BE RETURNED",
                },
                "reviewed_at": None,
                "updated_at": "2026-10-16T07:00:00Z",
            },
            {
                "letter_id": REVIEWED_ID,
                "structured_context": {"needs_reprocessing": True, "quality_flags": []},
                "reviewed_at": "2026-10-15T10:00:00Z",
                "updated_at": "2026-10-15T10:00:00Z",
            },
            {
                "letter_id": NORMAL_ID,
                "structured_context": {"needs_reprocessing": False, "quality_flags": []},
                "reviewed_at": None,
                "updated_at": "2026-10-14T10:00:00Z",
            },
        ]
        self.letters = {
            FLAGGED_ID: {
                "id": FLAGGED_ID,
                "title": "Synthetic review document",
                "original_filename": "synthetic.pdf",
                "authority": "Synthetic authority",
                "category": "notice",
                "issue_date": "2026-10-01",
                "reference_number": "REF-SYNTHETIC",
                "summary": "Synthetic summary",
                "is_trashed": False,
                "is_archived": False,
                "storage_object_id": "must-not-be-returned",
            },
            REVIEWED_ID: {"id": REVIEWED_ID, "title": "Already reviewed", "is_trashed": False},
            NORMAL_ID: {"id": NORMAL_ID, "title": "Normal record", "is_trashed": False},
        }
        self.updates: list[tuple[str, dict[str, object], dict[str, str]]] = []

    def select(self, table: str, filters=None, columns=None):
        filters = filters or {}
        if table == "letter_processing":
            rows = self.processing
            if "letter_id" in filters:
                rows = [row for row in rows if row["letter_id"] == filters["letter_id"]]
            return copy.deepcopy(rows)
        if table == "letters":
            rows = list(self.letters.values())
            if "id" in filters:
                rows = [row for row in rows if row["id"] == filters["id"]]
            return copy.deepcopy(rows)
        raise AssertionError(f"unexpected table read: {table}")

    def update(self, table: str, values: dict[str, object], *, filters: dict[str, str]):
        self.updates.append((table, copy.deepcopy(values), dict(filters)))
        if table != "letter_processing":
            raise AssertionError(f"unexpected table update: {table}")
        for row in self.processing:
            if row["letter_id"] == filters.get("letter_id"):
                row.update(copy.deepcopy(values))
                return copy.deepcopy(row)
        return {}


class QualityReviewQueueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = FakeReviewDatabase()
        self.membership = patch(
            "letter_registry.api._archive_membership",
            return_value=ArchiveMembership(
                archive_id=ARCHIVE_ID,
                user_id=ADMIN_ID,
                role=ArchiveRole.ADMIN,
            ),
        )
        self.membership.start()
        self.addCleanup(self.membership.stop)
        self.transport = patch("letter_registry.api._transport", side_effect=self._transport)
        self.transport.start()
        self.addCleanup(self.transport.stop)
        self.audit = patch("letter_registry.api._audit_admin_action")
        self.audit_mock = self.audit.start()
        self.addCleanup(self.audit.stop)
        self.client = TestClient(create_app(ApiDependencies()))
        self.headers = {"Authorization": "Bearer synthetic-admin-token"}

    def _transport(self, access_token: str, *, roles=None):
        if roles and ArchiveRole.ADMIN not in roles:
            raise AssertionError("unexpected role restriction")
        return self.db

    def test_queue_lists_only_unresolved_flagged_documents_and_sanitizes_fields(self) -> None:
        response = self.client.get("/api/v1/admin/review-queue", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["count"], 1)
        item = body["items"][0]
        self.assertEqual(item["letter_id"], FLAGGED_ID)
        self.assertEqual(item["title"], "Synthetic review document")
        self.assertIn("The document heading and body may refer to different topics.", item["review_reasons"])
        self.assertNotIn("clean_document_text", item)
        self.assertNotIn("storage_object_id", item)
        self.assertNotIn("extracted_text", item)

    def test_accepting_review_marks_metadata_reviewed_and_audits_decision(self) -> None:
        response = self.client.post(
            f"/api/v1/admin/review-queue/{FLAGGED_ID}/accept",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "reviewed")
        row = next(row for row in self.db.processing if row["letter_id"] == FLAGGED_ID)
        context = row["structured_context"]
        self.assertFalse(context["needs_reprocessing"])
        self.assertEqual(context["human_review"]["status"], "accepted_as_is")
        self.assertIsNotNone(row["reviewed_at"])
        self.assertEqual(len(self.db.updates), 1)
        self.audit_mock.assert_called_once()
        self.assertEqual(self.audit_mock.call_args.kwargs["action"], "document_quality_review_accepted")
        self.assertEqual(self.audit_mock.call_args.kwargs["target_id"], FLAGGED_ID)

    def test_accept_rejects_records_not_flagged_for_review(self) -> None:
        response = self.client.post(
            f"/api/v1/admin/review-queue/{NORMAL_ID}/accept",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.db.updates, [])
        self.audit_mock.assert_not_called()

    def test_accept_rejects_already_reviewed_record(self) -> None:
        response = self.client.post(
            f"/api/v1/admin/review-queue/{REVIEWED_ID}/accept",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.db.updates, [])

    def test_queue_fails_closed_when_admin_authorization_fails(self) -> None:
        with patch(
            "letter_registry.api._transport",
            side_effect=HTTPException(status_code=403, detail="Admin role required"),
        ):
            response = self.client.get("/api/v1/admin/review-queue", headers=self.headers)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.db.updates, [])

    def test_invalid_letter_id_is_rejected(self) -> None:
        response = self.client.post(
            "/api/v1/admin/review-queue/not-a-uuid/accept",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.db.updates, [])


if __name__ == "__main__":
    unittest.main()
