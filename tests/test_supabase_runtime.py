import json
import os
import unittest
from unittest.mock import patch

from letter_registry.supabase_runtime import (
    SupabasePostgrestTransport,
    SupabaseRuntimeError,
)


class SupabaseRuntimeTransportTests(unittest.TestCase):
    def test_from_environment_requires_runtime_only_values(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "SUPABASE_URL"):
                SupabasePostgrestTransport.from_environment()

    def test_worker_environment_prefers_direct_access_token(self) -> None:
        env = {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "synthetic-key",
            "SUPABASE_ACCESS_TOKEN": "synthetic-access",
            "SUPABASE_WORKER_EMAIL": "worker@example.com",
            "SUPABASE_WORKER_PASSWORD": "synthetic-password",
        }
        with patch.dict(os.environ, env, clear=True):
            transport = SupabasePostgrestTransport.from_worker_environment()

        self.assertEqual(transport.access_token, "synthetic-access")

    def test_worker_environment_signs_in_dedicated_account(self) -> None:
        from letter_registry.auth import SupabaseAuthSession

        env = {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "synthetic-key",
            "SUPABASE_WORKER_EMAIL": "worker@example.com",
            "SUPABASE_WORKER_PASSWORD": "synthetic-password",
        }
        with patch.dict(os.environ, env, clear=True):
            with patch(
                "letter_registry.auth.SupabasePasswordlessAuth.from_environment"
            ) as factory:
                factory.return_value.sign_in_with_password.return_value = (
                    SupabaseAuthSession(
                        access_token="fresh-worker-access",
                        refresh_token="rotating-refresh",
                        expires_in=3600,
                    )
                )
                transport = SupabasePostgrestTransport.from_worker_environment()

        self.assertEqual(transport.access_token, "fresh-worker-access")
        factory.return_value.sign_in_with_password.assert_called_once_with(
            email="worker@example.com",
            password="synthetic-password",
        )

    def test_worker_environment_requires_dedicated_credentials(self) -> None:
        env = {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "synthetic-key",
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(ValueError, "missing worker auth"):
                SupabasePostgrestTransport.from_worker_environment()

    def test_insert_sends_bearer_token_and_publishable_key(self) -> None:
        seen = {}

        def executor(req):
            seen["url"] = req.full_url
            seen["authorization"] = req.headers["Authorization"]
            seen["apikey"] = req.headers["Apikey"]
            seen["prefer"] = req.headers["Prefer"]
            seen["body"] = json.loads(req.data.decode("utf-8"))
            return 201, '[{"id":"synthetic-id"}]'

        transport = SupabasePostgrestTransport(
            base_url="https://example.supabase.co",
            publishable_key="synthetic-publishable-key",
            access_token="synthetic-user-token",
            http_executor=executor,
        )

        result = transport.insert(
            "letters",
            {"original_filename": "synthetic.pdf"},
            on_conflict="owner_id,original_sha256",
        )

        self.assertEqual(result["id"], "synthetic-id")
        self.assertIn("/rest/v1/letters?", seen["url"])
        self.assertEqual(seen["authorization"], "Bearer synthetic-user-token")
        self.assertEqual(seen["apikey"], "synthetic-publishable-key")
        self.assertIn("resolution=ignore-duplicates", seen["prefer"])

    def test_upsert_uses_merge_duplicate_resolution(self) -> None:
        seen = {}

        def executor(req):
            seen["prefer"] = req.headers["Prefer"]
            return 201, '[{"letter_id":"synthetic"}]'

        transport = SupabasePostgrestTransport(
            base_url="https://example.supabase.co",
            publishable_key="synthetic-key",
            access_token="synthetic-token",
            http_executor=executor,
        )

        transport.upsert(
            "letter_processing",
            {"letter_id": "synthetic"},
            on_conflict="letter_id",
        )

        self.assertIn("resolution=merge-duplicates", seen["prefer"])

    def test_update_uses_patch_and_filters(self) -> None:
        seen = {}

        def executor(req):
            seen["method"] = req.method
            seen["url"] = req.full_url
            seen["prefer"] = req.headers["Prefer"]
            seen["body"] = json.loads(req.data.decode("utf-8"))
            return 200, '[{"id":"synthetic","title":"Updated"}]'

        transport = SupabasePostgrestTransport(
            base_url="https://example.supabase.co",
            publishable_key="synthetic-key",
            access_token="synthetic-token",
            http_executor=executor,
        )

        result = transport.update(
            "letters",
            {"title": "Updated"},
            filters={"id": "synthetic"},
        )

        self.assertEqual(seen["method"], "PATCH")
        self.assertIn("id=eq.synthetic", seen["url"])
        self.assertEqual(seen["prefer"], "return=representation")
        self.assertEqual(result["title"], "Updated")

    def test_delete_returns_affected_rows(self) -> None:
        seen = {}

        def executor(req):
            seen["method"] = req.method
            seen["url"] = req.full_url
            seen["prefer"] = req.headers["Prefer"]
            return 200, '[{"id":"synthetic"}]'

        transport = SupabasePostgrestTransport(
            base_url="https://example.supabase.co",
            publishable_key="synthetic-key",
            access_token="synthetic-token",
            http_executor=executor,
        )

        rows = transport.delete("letters", filters={"id": "synthetic"})

        self.assertEqual(seen["method"], "DELETE")
        self.assertIn("id=eq.synthetic", seen["url"])
        self.assertEqual(seen["prefer"], "return=representation")
        self.assertEqual(rows, [{"id": "synthetic"}])

    def test_delete_empty_representation_means_no_rows_affected(self) -> None:
        def executor(req):
            return 200, "[]"

        transport = SupabasePostgrestTransport(
            base_url="https://example.supabase.co",
            publishable_key="synthetic-key",
            access_token="synthetic-token",
            http_executor=executor,
        )

        self.assertEqual(
            transport.delete("letters", filters={"id": "rls-hidden"}),
            [],
        )

    def test_delete_requires_filters(self) -> None:
        transport = SupabasePostgrestTransport(
            base_url="https://example.supabase.co",
            publishable_key="synthetic-key",
            access_token="synthetic-token",
            http_executor=lambda req: (200, "[]"),
        )
        with self.assertRaisesRegex(ValueError, "delete filters are required"):
            transport.delete("letters", filters={})

    def test_select_builds_eq_filters(self) -> None:
        seen = {}

        def executor(req):
            seen["url"] = req.full_url
            return 200, '[{"id":"synthetic"}]'

        transport = SupabasePostgrestTransport(
            base_url="https://example.supabase.co",
            publishable_key="synthetic-key",
            access_token="synthetic-token",
            http_executor=executor,
        )

        rows = transport.select(
            "letters",
            filters={"original_sha256": "abc"},
            columns="id,original_sha256",
        )

        self.assertEqual(rows[0]["id"], "synthetic")
        self.assertIn("original_sha256=eq.abc", seen["url"])

    def test_rpc_posts_parameters(self) -> None:
        seen = {}

        def executor(req):
            seen["url"] = req.full_url
            seen["body"] = json.loads(req.data.decode("utf-8"))
            return 200, '[{"id":"synthetic"}]'

        transport = SupabasePostgrestTransport(
            base_url="https://example.supabase.co",
            publishable_key="synthetic-key",
            access_token="synthetic-token",
            http_executor=executor,
        )

        rows = transport.rpc(
            "search_letters",
            {"search_query": "inter exam", "result_limit": 10},
        )

        self.assertEqual(rows[0]["id"], "synthetic")
        self.assertTrue(seen["url"].endswith("/rest/v1/rpc/search_letters"))
        self.assertEqual(seen["body"]["result_limit"], 10)

    def test_non_success_status_raises(self) -> None:
        def executor(req):
            return 401, '{"message":"denied"}'

        transport = SupabasePostgrestTransport(
            base_url="https://example.supabase.co",
            publishable_key="synthetic-key",
            access_token="synthetic-token",
            http_executor=executor,
        )

        with self.assertRaises(SupabaseRuntimeError):
            transport.select("letters")


if __name__ == "__main__":
    unittest.main()
