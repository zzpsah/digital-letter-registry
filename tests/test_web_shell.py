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

    def test_admin_operations_failure_retry_panel_is_exposed(self) -> None:
        self.assertIn('data-admin-pane="operations"', self.html)
        self.assertIn('id="operationsList"', self.html)
        self.assertIn('fetch("/api/v1/admin/operations"', self.html)
        self.assertIn('data-retry-job', self.html)

    def test_admin_soft_delete_restore_controls_are_exposed(self) -> None:
        self.assertIn("data-restore-recipient", self.html)
        self.assertIn("data-purge-recipient", self.html)
        self.assertIn("data-restore-category", self.html)
        self.assertIn("data-toggle-member", self.html)

    def test_admin_backup_restore_and_bulk_controls_are_exposed(self) -> None:
        self.assertIn('data-admin-pane="backup"', self.html)
        self.assertIn('id="exportAdminBackup"', self.html)
        self.assertIn('id="restoreBackupFile"', self.html)
        self.assertIn('id="restoreAdminBackup"', self.html)
        self.assertIn('data-select-member', self.html)
        self.assertIn('data-select-recipient', self.html)
        self.assertIn('data-select-category', self.html)
        self.assertIn('fetch("/api/v1/admin/backup/preview"', self.html)
        self.assertIn('fetch("/api/v1/admin/backup/restore"', self.html)

    def test_portal_refresh_and_auto_sync_controls_are_exposed(self) -> None:
        self.assertIn('id="refreshDashboard"', self.html)
        self.assertIn('id="refreshLibrary"', self.html)
        self.assertIn('id="portalSyncStatus"', self.html)
        self.assertIn('setInterval(()=>', self.html)
        self.assertIn('document.addEventListener("visibilitychange"', self.html)
        self.assertIn('Date.now()', self.html)

    def test_sorting_and_important_highlight_controls_are_exposed(self) -> None:
        self.assertIn('id="sortOrder"', self.html)
        self.assertIn('Latest first', self.html)
        self.assertIn('Important first', self.html)
        self.assertIn('data-star=', self.html)
        self.assertIn('data-edit-note=', self.html)
        self.assertIn('/highlight', self.html)
        self.assertIn('class="star ', self.html)
        self.assertIn('user-note', self.html)
        self.assertIn('upload-date', self.html)
        self.assertIn('displayUploadDate', self.html)

    def test_login_remember_me_and_hinglish_card_priority(self) -> None:
        self.assertIn('id="rememberMe"', self.html)
        self.assertIn('Remember me on this device', self.html)
        self.assertIn('remember_me:', self.html)
        self.assertIn('r.summary_hi||r.summary', self.html)
        self.assertIn('r.action_required_hi||r.action_required', self.html)

    def test_language_toggle_and_smart_search_are_exposed(self) -> None:
        self.assertIn('id="languageMode"', self.html)
        self.assertIn('value="mixed"', self.html)
        self.assertIn('value="hi"', self.html)
        self.assertIn('value="en"', self.html)
        self.assertIn('elettersLanguage', self.html)
        self.assertIn('Smart Search', self.html)
        self.assertIn('displayLanguage==="en"', self.html)
        self.assertIn('displayLanguage==="hi"', self.html)

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
