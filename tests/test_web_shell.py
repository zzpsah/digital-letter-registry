from pathlib import Path
import unittest


class WebShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = (
            Path(__file__).parents[1]
            / "src"
            / "letter_registry"
            / "web"
            / "index.html"
        ).read_text(encoding="utf-8")

    def test_web_shell_uses_server_side_cookie_session(self) -> None:
        self.assertIn('fetch("/api/v1/auth/session"', self.html)
        self.assertNotIn('fragment.get("access_token")', self.html)
        self.assertNotIn('sessionStorage.setItem("dlr_access_token"', self.html)
        self.assertNotIn('localStorage.setItem("dlr_access_token"', self.html)

    def test_browser_never_persists_refresh_token(self) -> None:
        self.assertNotIn('sessionStorage.setItem("dlr_refresh_token"', self.html)
        self.assertNotIn('localStorage.setItem("dlr_refresh_token"', self.html)

    def test_authenticated_user_can_set_or_change_password(self) -> None:
        self.assertIn('id="passwordChangeForm"', self.html)
        self.assertIn(
            'fetch("/api/v1/auth/password/change"',
            self.html,
        )
        self.assertIn('id="confirmPassword"', self.html)

    def test_admin_approved_account_request_and_activation_are_exposed(self) -> None:
        self.assertIn("<summary>Request Access</summary>", self.html)
        self.assertNotIn('id="registerConfirmPassword"', self.html)
        self.assertIn(
            'fetch("/api/v1/auth/create-account"',
            self.html,
        )
        self.assertIn('id="approvedSetupForm"', self.html)
        self.assertIn(
            'fetch("/api/v1/auth/complete-approved-account"',
            self.html,
        )
        self.assertIn('data-admin-pane="recipients"', self.html)
        self.assertIn('data-admin-pane="whatsapp"', self.html)

    def test_magic_link_controls_are_not_in_primary_ui(self) -> None:
        self.assertNotIn('id="loginForm"', self.html)
        self.assertNotIn('id="registerMagicLink"', self.html)
        self.assertNotIn('data-send-invite-email=', self.html)

    def test_streamed_original_response_is_opened_from_blob(self) -> None:
        self.assertIn("const blob=await res.blob()", self.html)
        self.assertIn("URL.createObjectURL(blob)", self.html)

    def test_sign_out_uses_server_cookie_clear_endpoint(self) -> None:
        self.assertIn(
            'fetch("/api/v1/auth/logout",{method:"POST"})',
            self.html,
        )
        self.assertNotIn('sessionStorage.removeItem("dlr_access_token")', self.html)


    def test_web_shell_exposes_real_intake_pilot_indicator(self):
        self.assertIn("PILOT MODE", self.html)
        self.assertIn("pilot_remaining", self.html)
        self.assertIn("pilot_limit", self.html)

    def test_service_worker_registration_bypasses_http_cache(self):
        self.assertIn('register("/sw.js?v=2",{updateViaCache:"none"})', self.html)

if __name__ == "__main__":
    unittest.main()
