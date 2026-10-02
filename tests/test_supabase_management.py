import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from letter_registry.supabase_management import (
    SupabaseAuthConfigManager,
    _merge_allow_list,
    _project_ref_from_url,
)


class SupabaseManagementTests(unittest.TestCase):
    def test_project_ref_is_derived_from_hosted_url(self):
        self.assertEqual(
            _project_ref_from_url("https://example-ref.supabase.co"),
            "example-ref",
        )

    def test_allow_list_preserves_existing_entries(self):
        self.assertEqual(
            _merge_allow_list(
                "https://one.example/cb,https://two.example/cb",
                "https://archive.example.com/auth/confirm",
            ),
            "https://one.example/cb,https://two.example/cb,"
            "https://archive.example.com/auth/confirm",
        )

    def test_apply_patches_only_drift_and_preserves_allow_list(self):
        calls = []
        current = {
            "site_url": "http://localhost:3000",
            "uri_allow_list": "https://existing.example/callback",
            "mailer_subjects_magic_link": "Old subject",
            "mailer_templates_magic_link_content": "old",
        }

        def executor(req):
            calls.append(req)
            if req.method == "GET":
                return 200, json.dumps(current)
            payload = json.loads(req.data.decode("utf-8"))
            current.update(payload)
            return 200, json.dumps(current)

        manager = SupabaseAuthConfigManager(
            project_ref="example-ref",
            management_token="secret-token",
            site_url="https://archive.example.com",
            redirect_url="https://archive.example.com/auth/confirm",
            template_html="<a>synthetic template</a>",
            http_executor=executor,
        )

        changed = manager.apply()
        self.assertEqual(
            set(changed),
            {
                "site_url",
                "uri_allow_list",
                "mailer_subjects_magic_link",
                "mailer_templates_magic_link_content",
            },
        )
        self.assertIn(
            "https://existing.example/callback",
            current["uri_allow_list"],
        )
        self.assertIn(
            "https://archive.example.com/auth/confirm",
            current["uri_allow_list"],
        )
        self.assertEqual(calls[1].method, "PATCH")

    def test_environment_loader_never_requires_project_ref_secret(self):
        with tempfile.TemporaryDirectory() as td:
            template = Path(td) / "magic.html"
            template.write_text("{{ .TokenHash }}", encoding="utf-8")
            env = {
                "SUPABASE_MANAGEMENT_ACCESS_TOKEN": "secret-token",
                "SUPABASE_URL": "https://example-ref.supabase.co",
                "AUTH_REDIRECT_URL": "https://archive.example.com/auth/confirm",
            }
            with patch.dict(os.environ, env, clear=False):
                manager = SupabaseAuthConfigManager.from_environment(
                    template_path=template
                )
        self.assertEqual(manager.project_ref, "example-ref")
        self.assertEqual(manager.site_url, "https://archive.example.com")


if __name__ == "__main__":
    unittest.main()
