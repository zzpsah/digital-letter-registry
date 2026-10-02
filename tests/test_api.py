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
                {"AUTH_REDIRECT_URL": "https://archive.example.com/auth/confirm"},
                clear=False,
            ):
                response = self.client.post(
                    "/api/v1/auth/magic-link",
                    json={"email": "owner@example.com"},
                    headers={"Origin": "https://archive.example.com"},
                )

        self.assertEqual(response.status_code, 200)
        auth.send_magic_link.assert_called_once_with(
            email="owner@example.com",
            redirect_to="https://archive.example.com/auth/confirm",
        )

    def test_magic_link_callback_sets_httponly_session_cookies(self):
        from letter_registry.auth import SupabaseAuthSession

        with patch(
            "letter_registry.api.SupabasePasswordlessAuth.from_environment"
        ) as factory:
            factory.return_value.verify_token_hash.return_value = (
                SupabaseAuthSession(
                    access_token="synthetic-access",
                    refresh_token="synthetic-refresh",
                    expires_in=3600,
                )
            )
            with patch.dict(
                os.environ,
                {"AUTH_COOKIE_SECURE": "false"},
                clear=False,
            ):
                response = self.client.get(
                    "/auth/confirm"
                    "?token_hash=synthetic-hash&type=email",
                    follow_redirects=False,
                )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "/")
        cookies = response.headers.get_list("set-cookie")
        joined = "\n".join(cookies).lower()
        self.assertIn("dlr_access_token=", joined)
        self.assertIn("dlr_refresh_token=", joined)
        self.assertIn("httponly", joined)
        self.assertIn("samesite=lax", joined)
        self.assertEqual(
            response.headers["cache-control"],
            "private, no-store",
        )

    def test_cookie_authenticated_search_needs_no_bearer_header(self):
        fake = FakeTransport()
        self.client.cookies.set(
            "dlr_access_token",
            "synthetic-cookie-access",
        )
        with patch("letter_registry.api._transport", return_value=fake):
            with patch.dict(
                os.environ,
                {"GEMINI_API_KEY": ""},
                clear=False,
            ):
                response = self.client.get("/api/v1/search?q=inter")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)

    def test_logout_clears_session_cookies(self):
        self.client.cookies.set(
            "dlr_access_token",
            "synthetic-cookie-access",
        )
        self.client.cookies.set(
            "dlr_refresh_token",
            "synthetic-cookie-refresh",
        )

        with patch.dict(
            os.environ,
            {"AUTH_REDIRECT_URL": "https://archive.example.com/auth/confirm"},
            clear=False,
        ):
            response = self.client.post(
                "/api/v1/auth/logout",
                headers={"Origin": "https://archive.example.com"},
            )

        self.assertEqual(response.status_code, 200)
        joined = "\n".join(
            response.headers.get_list("set-cookie")
        ).lower()
        self.assertIn("dlr_access_token=", joined)
        self.assertIn("dlr_refresh_token=", joined)
        self.assertIn("max-age=0", joined)

    def test_cross_site_cookie_mutation_is_rejected(self):
        self.client.cookies.set(
            "dlr_access_token",
            "synthetic-cookie-access",
        )
        with patch.dict(
            os.environ,
            {"AUTH_REDIRECT_URL": "https://archive.example.com/auth/confirm"},
            clear=False,
        ):
            response = self.client.post(
                "/api/v1/auth/logout",
                headers={"Origin": "https://attacker.example"},
            )

        self.assertEqual(response.status_code, 403)
        self.assertIn("Cross-site", response.json()["detail"])

    def test_bearer_mutation_does_not_require_origin_header(self):
        class RelationshipTransport:
            def rpc(self, function, params):
                return [{"success": True}]

            def select(self, table, *, filters=None, columns="*"):
                return []

        with patch(
            "letter_registry.api._transport",
            return_value=RelationshipTransport(),
        ):
            response = self.client.post(
                "/api/v1/relationships/"
                "44444444-4444-4444-8444-444444444444/review",
                headers={"Authorization": "Bearer synthetic-user-token"},
                json={"decision": "confirmed"},
            )

        self.assertEqual(response.status_code, 200)

    def test_capabilities_report_synthetic_mode_and_refresh_drive_config(self):
        env = {
            "ENABLE_REAL_INTAKE": "false",
            "GOOGLE_OAUTH_CLIENT_ID": "synthetic-client",
            "GOOGLE_OAUTH_CLIENT_SECRET": "synthetic-secret",
            "GOOGLE_DRIVE_REFRESH_TOKEN": "synthetic-refresh",
            "DRIVE_ORIGINALS_FOLDER_REFERENCE": "synthetic-folder",
            "GEMINI_API_KEY": "synthetic-gemini",
            "AUTH_COOKIE_SECURE": "true",
        }
        with patch.dict(os.environ, env, clear=False):
            with patch("letter_registry.api._transport", return_value=object()):
                response = self.client.get(
                    "/api/v1/capabilities",
                    headers={"Authorization": "Bearer synthetic-user-token"},
                )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["synthetic_only"])
        self.assertTrue(body["drive_upload_configured"])
        self.assertTrue(body["original_streaming_configured"])
        self.assertTrue(body["semantic_search_configured"])
        self.assertTrue(body["auth_cookie_secure"])

    def test_capabilities_do_not_expose_runtime_secret_values(self):
        with patch.dict(
            os.environ,
            {
                "GOOGLE_DRIVE_ACCESS_TOKEN": "very-secret-token",
                "DRIVE_ORIGINALS_FOLDER_REFERENCE": "private-folder-id",
            },
            clear=False,
        ):
            with patch("letter_registry.api._transport", return_value=object()):
                response = self.client.get(
                    "/api/v1/capabilities",
                    headers={"Authorization": "Bearer synthetic-user-token"},
                )

        serialized = response.text
        self.assertNotIn("very-secret-token", serialized)
        self.assertNotIn("private-folder-id", serialized)

    def test_pwa_manifest_and_service_worker_are_public(self):
        self.assertEqual(self.client.get("/manifest.webmanifest").status_code, 200)
        self.assertEqual(self.client.get("/sw.js").status_code, 200)

    def test_synthetic_intake_returns_archive_and_job_ids_only(self):
        from letter_registry.channel_intake import ChannelIntakeService
        from letter_registry.intake import IntakeService
        from letter_registry.jobs import InMemoryProcessingQueue
        from letter_registry.persistence import InMemoryLetterRepository
        from letter_registry.storage import InMemoryOriginalStorage

        class Provenance:
            def save_source(self, *, owner_id, letter_id, provenance):
                pass

        service = ChannelIntakeService(
            intake=IntakeService(
                storage=InMemoryOriginalStorage(),
                repository=InMemoryLetterRepository(),
                queue=InMemoryProcessingQueue(),
            ),
            provenance=Provenance(),
        )

        with patch(
            "letter_registry.api._runtime_intake",
            return_value=(
                "11111111-1111-4111-8111-111111111111",
                service,
            ),
        ):
            response = self.client.post(
                "/api/v1/intake",
                headers={"Authorization": "Bearer synthetic-user-token"},
                files={
                    "file": (
                        "synthetic-upload.pdf",
                        b"%PDF-synthetic-upload",
                        "application/pdf",
                    )
                },
            )

        self.assertEqual(response.status_code, 202)
        body = response.json()
        self.assertEqual(body["original_filename"], "synthetic-upload.pdf")
        self.assertEqual(body["job_status"], "pending")
        self.assertTrue(body["synthetic_only"])
        self.assertEqual(len(body["sha256"]), 64)
        self.assertNotIn("storage_object_id", body)
        self.assertNotIn("storage_reference", body)

    def test_real_looking_upload_is_blocked_by_default(self):
        from letter_registry.channel_intake import ChannelIntakeService
        from letter_registry.intake import IntakeService
        from letter_registry.jobs import InMemoryProcessingQueue
        from letter_registry.persistence import InMemoryLetterRepository
        from letter_registry.storage import InMemoryOriginalStorage

        class Provenance:
            def save_source(self, *, owner_id, letter_id, provenance):
                pass

        service = ChannelIntakeService(
            intake=IntakeService(
                storage=InMemoryOriginalStorage(),
                repository=InMemoryLetterRepository(),
                queue=InMemoryProcessingQueue(),
            ),
            provenance=Provenance(),
        )

        with patch(
            "letter_registry.api._runtime_intake",
            return_value=(
                "11111111-1111-4111-8111-111111111111",
                service,
            ),
        ):
            response = self.client.post(
                "/api/v1/intake",
                headers={"Authorization": "Bearer synthetic-user-token"},
                files={
                    "file": (
                        "official-letter.pdf",
                        b"%PDF-real-looking",
                        "application/pdf",
                    )
                },
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("real document intake is disabled", response.json()["detail"])

    def test_intake_requires_bearer_session(self):
        response = self.client.post(
            "/api/v1/intake",
            files={
                "file": (
                    "synthetic.pdf",
                    b"%PDF-synthetic",
                    "application/pdf",
                )
            },
        )
        self.assertEqual(response.status_code, 401)

    def test_processing_versions_endpoint(self):
        with patch("letter_registry.api._transport", return_value=object()):
            response = self.client.get(
                "/api/v1/processing/versions",
                headers={"Authorization": "Bearer synthetic-user-token"},
            )

        self.assertEqual(response.status_code, 200)
        versions = response.json()["versions"]
        self.assertEqual(versions["filename_rule_version"], "official-v1")
        self.assertEqual(versions["status_rule_version"], "relationships-v1")

    def test_reprocessing_preview_uses_current_registry_defaults(self):
        class PreviewTransport:
            def select(self, table, *, filters=None, columns="*"):
                return [{
                    "letter_id": "22222222-2222-4222-8222-222222222222",
                    "ocr_version": "old-ocr",
                    "context_version": "old-context",
                    "dictionary_version": "old-dict",
                    "filename_rule_version": "old-name",
                    "category_schema_version": "old-cat",
                    "embedding_version": "old-embed",
                    "status_rule_version": "old-status",
                }]

        with patch("letter_registry.api._transport", return_value=PreviewTransport()):
            response = self.client.get(
                "/api/v1/reprocessing/preview",
                headers={"Authorization": "Bearer synthetic-user-token"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        target = response.json()["items"][0]["target_versions"]
        self.assertEqual(target["filename_rule_version"], "official-v1")

    def test_reprocessing_preview_is_read_only(self):
        class PreviewTransport:
            def select(self, table, *, filters=None, columns="*"):
                return [{
                    "letter_id": "22222222-2222-4222-8222-222222222222",
                    "ocr_version": "ocr-v1",
                    "context_version": "context-v1",
                    "dictionary_version": "dict-v1",
                    "filename_rule_version": "name-v1",
                    "category_schema_version": "cat-v1",
                    "embedding_version": "embed-v1",
                    "status_rule_version": "status-v1",
                }]

        with patch("letter_registry.api._transport", return_value=PreviewTransport()):
            response = self.client.get(
                "/api/v1/reprocessing/preview"
                "?ocr_version=ocr-v2"
                "&context_version=context-v2"
                "&dictionary_version=dict-v2"
                "&filename_rule_version=name-v2"
                "&category_schema_version=cat-v2"
                "&embedding_version=embed-v2"
                "&status_rule_version=status-v2",
                headers={"Authorization": "Bearer synthetic-user-token"},
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["count"], 1)
        self.assertIn("ocr_version", body["items"][0]["reasons"])

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
        self.assertEqual(fake.last_function, "search_letter_cards")
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

    def test_relationship_review_endpoint(self):
        class RelationshipTransport:
            def rpc(self, function, params):
                return [{"success": True}]

            def select(self, table, *, filters=None, columns="*"):
                return []

        with patch("letter_registry.api._transport", return_value=RelationshipTransport()):
            response = self.client.post(
                "/api/v1/relationships/44444444-4444-4444-8444-444444444444/review",
                headers={"Authorization": "Bearer synthetic-user-token"},
                json={"decision": "confirmed"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["message"],
            "Relationship confirmed.",
        )

    def test_relationship_review_rejects_suggested_decision(self):
        response = self.client.post(
            "/api/v1/relationships/44444444-4444-4444-8444-444444444444/review",
            headers={"Authorization": "Bearer synthetic-user-token"},
            json={"decision": "suggested"},
        )
        self.assertEqual(response.status_code, 400)

    def test_original_endpoint_streams_private_bytes_without_storage_id(self):
        from letter_registry.original_access import OriginalFile, SupabaseOriginalAccessService

        class Database:
            def select(self, table, *, filters=None, columns="*"):
                return [{
                    "original_filename": "synthetic.pdf",
                    "storage_provider": "gdrive",
                    "storage_object_id": "private-object-reference",
                }]

        class Storage:
            def download(self, *, provider, object_reference, filename):
                return OriginalFile(
                    filename=filename,
                    content_type="application/pdf",
                    content=b"%PDF-synthetic",
                )

        app = create_app(
            ApiDependencies(
                original_access=SupabaseOriginalAccessService(Storage())
            )
        )
        client = TestClient(app)
        with patch("letter_registry.api._transport", return_value=Database()):
            response = client.get(
                "/api/v1/letters/22222222-2222-4222-8222-222222222222/original",
                headers={"Authorization": "Bearer synthetic-user-token"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"%PDF-synthetic")
        self.assertEqual(response.headers["cache-control"], "private, no-store")
        self.assertIn("synthetic.pdf", response.headers["content-disposition"])
        self.assertNotIn("private-object-reference", str(response.headers))
        self.assertNotIn(b"private-object-reference", response.content)

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
        self.assertIn("पत्र जोड़ें", response.text)
        self.assertIn("uploadForm", response.text)


if __name__ == "__main__":
    unittest.main()
