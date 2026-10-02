import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from letter_registry.api import ApiDependencies, create_app


class FakeTransport:
    def rpc(self, function, params):
        self.last_function = function
        self.last_params = params
        return [
            {
                "id": "22222222-2222-4222-8222-222222222222",
                "smart_filename": "inter-exam__bseb__2026-10-01__REF-1.pdf",
                "title": "Inter Exam Extension",
                "authority": "BSEB",
                "category": "exam",
                "issue_date": "2026-10-01",
                "status": "current",
                "action_required": "Complete form",
                "concepts": ["exam_form"],
                "context_snippet": "Synthetic context",
                "file_type": "pdf",
                "text_rank": 0.7,
                "fuzzy_rank": 0.3,
                "combined_rank": 0.6,
            }
        ]


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(ApiDependencies())
        self.client = TestClient(self.app)

    def test_health_is_public(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_magic_link_request_uses_runtime_redirect(self):
        with patch("letter_registry.api.SupabasePasswordlessAuth.from_environment") as factory:
            auth = factory.return_value
            with patch.dict(
                os.environ,
                {"AUTH_REDIRECT_URL": "https://archive.example.com/auth/callback"},
                clear=False,
            ):
                response = self.client.post(
                    "/api/v1/auth/magic-link",
                    json={"email": "owner@example.com"},
                )

        self.assertEqual(response.status_code, 200)
        auth.send_magic_link.assert_called_once_with(
            email="owner@example.com",
            redirect_to="https://archive.example.com/auth/callback",
        )

    def test_pwa_manifest_and_service_worker_are_public(self):
        self.assertEqual(self.client.get("/manifest.webmanifest").status_code, 200)
        self.assertEqual(self.client.get("/sw.js").status_code, 200)

    def test_search_requires_bearer_session(self):
        response = self.client.get("/api/v1/search?q=inter")
        self.assertEqual(response.status_code, 401)

    def test_authenticated_text_search_returns_safe_card(self):
        fake = FakeTransport()
        with patch("letter_registry.api._transport", return_value=fake):
            with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
                response = self.client.get(
                    "/api/v1/search?q=inter&year=2026&status=current&file_type=pdf",
                    headers={"Authorization": "Bearer synthetic-user-token"},
                )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["mode"], "text")
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["results"][0]["file_type"], "pdf")
        self.assertEqual(
            body["results"][0]["open_original_path"],
            "/api/v1/letters/22222222-2222-4222-8222-222222222222/original",
        )
        self.assertNotIn("storage_object_id", body["results"][0])
        self.assertEqual(fake.last_function, "search_letters_filtered")
        self.assertEqual(fake.last_params["year_filter"], 2026)

    def test_authenticated_letter_detail_excludes_storage_reference(self):
        class DetailTransport:
            def select(self, table, *, filters=None, columns="*"):
                if table == "letters":
                    return [{
                        "id": "22222222-2222-4222-8222-222222222222",
                        "smart_filename": "synthetic.pdf",
                        "title": "Synthetic",
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

        with patch("letter_registry.api._transport", return_value=DetailTransport()):
            response = self.client.get(
                "/api/v1/letters/22222222-2222-4222-8222-222222222222",
                headers={"Authorization": "Bearer synthetic-user-token"},
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["title"], "Synthetic")
        self.assertNotIn("storage_object_id", body)

    def test_original_endpoint_is_closed_until_private_resolver_exists(self):
        response = self.client.get(
            "/api/v1/letters/22222222-2222-4222-8222-222222222222/original",
            headers={"Authorization": "Bearer synthetic-user-token"},
        )
        self.assertEqual(response.status_code, 501)

    def test_home_serves_hindi_first_interface(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("आधिकारिक पत्र खोज", response.text)


if __name__ == "__main__":
    unittest.main()
