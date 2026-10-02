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

    def test_magic_link_fragment_is_captured_client_side(self) -> None:
        self.assertIn('fragment.get("access_token")', self.html)
        self.assertIn('fragment.get("token_type")', self.html)
        self.assertIn('sessionStorage.setItem("dlr_access_token"', self.html)
        self.assertIn('history.replaceState(null,"",location.pathname+location.search)', self.html)

    def test_refresh_token_is_not_persisted_by_web_shell(self) -> None:
        self.assertNotIn('sessionStorage.setItem("dlr_refresh_token"', self.html)
        self.assertNotIn('localStorage.setItem("dlr_access_token"', self.html)

    def test_streamed_original_response_is_opened_from_blob(self) -> None:
        self.assertIn("const blob=await res.blob()", self.html)
        self.assertIn("URL.createObjectURL(blob)", self.html)

    def test_sign_out_clears_browser_session(self) -> None:
        self.assertIn('sessionStorage.removeItem("dlr_access_token")', self.html)


if __name__ == "__main__":
    unittest.main()
