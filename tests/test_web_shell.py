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
