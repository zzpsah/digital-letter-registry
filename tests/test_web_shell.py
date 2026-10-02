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

    def test_admin_can_send_pending_registration_email(self) -> None:
        self.assertIn('data-send-invite-email=', self.html)
        self.assertIn(
            'fetch("/api/v1/auth/register-magic-link"',
            self.html,
        )

    def test_invite_secret_uses_fragment_and_is_cleared(self) -> None:
        self.assertIn('"/#invite="', self.html)
        self.assertIn("location.hash.slice(1)", self.html)
        self.assertIn("history.replaceState", self.html)
        self.assertNotIn('location.search).get("invite")', self.html)

    def test_streamed_original_response_is_opened_from_blob(self) -> None:
        self.assertIn("const blob=await res.blob()", self.html)
        self.assertIn("URL.createObjectURL(blob)", self.html)

    def test_sign_out_uses_server_cookie_clear_endpoint(self) -> None:
        self.assertIn(
            'fetch("/api/v1/auth/logout",{method:"POST"})',
            self.html,
        )
        self.assertNotIn('sessionStorage.removeItem("dlr_access_token")', self.html)


if __name__ == "__main__":
    unittest.main()
