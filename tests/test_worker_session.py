"""Worker session reuse, refresh rotation, and cross-process race safety."""

import json
import os
import tempfile
import time
import unittest
from unittest.mock import patch

from letter_registry.auth import SupabaseAuthSession
from letter_registry.worker_session import (
    DEFAULT_EXPIRY_MARGIN_SECONDS,
    WorkerSession,
    WorkerSessionError,
    load_worker_session,
    session_status,
)


class FakeAuth:
    """Records which grant each call used; returns rotating tokens."""

    def __init__(self, *, fail_refresh: bool = False):
        self.password_calls: list[dict[str, str]] = []
        self.refresh_calls: list[str] = []
        self.fail_refresh = fail_refresh
        self._n = 0

    def _next(self) -> SupabaseAuthSession:
        self._n += 1
        return SupabaseAuthSession(
            access_token=f"access-{self._n}",
            refresh_token=f"refresh-{self._n}",
            expires_in=3600,
        )

    def sign_in_with_password(self, *, email: str, password: str):
        self.password_calls.append({"email": email, "password": password})
        return self._next()

    def refresh_session(self, *, refresh_token: str):
        self.refresh_calls.append(refresh_token)
        if self.fail_refresh:
            raise RuntimeError("refresh rejected")
        return self._next()


class WorkerSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.state = os.path.join(self._tmp.name, "worker-session.json")
        self.lock = os.path.join(self._tmp.name, "worker-session.lock")
        self.env = patch.dict(
            os.environ,
            {
                "DLR_WORKER_SESSION_FILE": self.state,
                "DLR_WORKER_SESSION_LOCK": self.lock,
            },
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    def load(self, auth, **kwargs):
        return load_worker_session(
            auth_factory=lambda: auth,
            email="worker@example.com",
            password="synthetic-password",
            **kwargs,
        )

    def test_first_call_uses_password_grant(self) -> None:
        auth = FakeAuth()
        session = self.load(auth)
        self.assertEqual(session.source, "password")
        self.assertEqual(len(auth.password_calls), 1)
        self.assertEqual(auth.refresh_calls, [])

    def test_second_call_reuses_cache_without_any_auth(self) -> None:
        """The defect: N runs must not produce N password grants."""
        auth = FakeAuth()
        first = self.load(auth)
        for _ in range(20):
            later = self.load(auth)
            self.assertEqual(later.access_token, first.access_token)
            self.assertEqual(later.source, "cache")
        self.assertEqual(len(auth.password_calls), 1)
        self.assertEqual(auth.refresh_calls, [])

    def test_expiring_token_is_refreshed_not_password_signed_in(self) -> None:
        auth = FakeAuth()
        self.load(auth)
        # Force the cached session inside the expiry margin.
        raw = json.loads(open(self.state, encoding="utf-8").read())
        raw["expires_at"] = time.time() + DEFAULT_EXPIRY_MARGIN_SECONDS - 10
        open(self.state, "w", encoding="utf-8").write(json.dumps(raw))

        refreshed = self.load(auth)
        self.assertEqual(refreshed.source, "refresh")
        self.assertEqual(auth.refresh_calls, ["refresh-1"])
        self.assertEqual(len(auth.password_calls), 1, "must not re-use password grant")

    def test_refreshed_token_is_persisted_for_the_next_run(self) -> None:
        auth = FakeAuth()
        self.load(auth)
        raw = json.loads(open(self.state, encoding="utf-8").read())
        raw["expires_at"] = time.time() + DEFAULT_EXPIRY_MARGIN_SECONDS - 10
        open(self.state, "w", encoding="utf-8").write(json.dumps(raw))

        refreshed = self.load(auth)
        again = self.load(auth)
        self.assertEqual(again.access_token, refreshed.access_token)
        self.assertEqual(again.source, "cache")
        self.assertEqual(len(auth.refresh_calls), 1)

    def test_failed_refresh_falls_back_to_password_once(self) -> None:
        auth = FakeAuth(fail_refresh=True)
        self.load(auth)
        raw = json.loads(open(self.state, encoding="utf-8").read())
        raw["expires_at"] = time.time() + DEFAULT_EXPIRY_MARGIN_SECONDS - 10
        open(self.state, "w", encoding="utf-8").write(json.dumps(raw))

        recovered = self.load(auth)
        self.assertEqual(recovered.source, "password")
        self.assertEqual(auth.refresh_calls, ["refresh-1"])
        self.assertEqual(len(auth.password_calls), 2)

    def test_refresh_only_never_uses_password(self) -> None:
        """Health checks must not be able to trigger a password grant."""
        auth = FakeAuth()
        with self.assertRaises(WorkerSessionError):
            self.load(auth, refresh_only=True)
        self.assertEqual(auth.password_calls, [])

    def test_refresh_only_reuses_a_valid_cache(self) -> None:
        auth = FakeAuth()
        self.load(auth)
        status = session_status()
        self.assertTrue(status["present"])
        self.assertTrue(status["usable"])
        self.assertNotIn("access_token", status)

    def test_corrupt_cache_is_ignored_not_fatal(self) -> None:
        open(self.state, "w", encoding="utf-8").write("{not json")
        auth = FakeAuth()
        session = self.load(auth)
        self.assertEqual(session.source, "password")

    def test_cache_file_is_owner_only(self) -> None:
        auth = FakeAuth()
        self.load(auth)
        mode = os.stat(self.state).st_mode & 0o777
        self.assertEqual(mode, 0o600, f"expected 0600, got {oct(mode)}")

    def test_state_dir_is_owner_only(self) -> None:
        auth = FakeAuth()
        self.load(auth)
        mode = os.stat(os.path.dirname(self.state)).st_mode & 0o777
        self.assertEqual(mode, 0o700, f"expected 0700, got {oct(mode)}")

    def test_old_expired_cache_keeps_refresh_token(self) -> None:
        auth = FakeAuth()
        self.load(auth)
        raw = json.loads(open(self.state, encoding="utf-8").read())
        raw["written_at"] = time.time() - 7200
        raw["expires_at"] = raw["written_at"] + 3600 - 1
        with open(self.state, "w", encoding="utf-8") as handle:
            json.dump(raw, handle)

        refreshed = self.load(auth)
        self.assertEqual(refreshed.source, "refresh")
        self.assertEqual(auth.refresh_calls, ["refresh-1"])
        self.assertEqual(len(auth.password_calls), 1)

    def test_quota_402_pauses_auth_and_does_not_fall_back_to_password(self) -> None:
        class QuotaAuth(FakeAuth):
            def refresh_session(self, *, refresh_token: str):
                self.refresh_calls.append(refresh_token)
                raise RuntimeError(
                    "Supabase Auth failed with HTTP 402: exceed_egress_quota"
                )

        seed_auth = FakeAuth()
        self.load(seed_auth)
        raw = json.loads(open(self.state, encoding="utf-8").read())
        raw["expires_at"] = time.time() - 60
        with open(self.state, "w", encoding="utf-8") as handle:
            json.dump(raw, handle)

        auth = QuotaAuth()
        with self.assertRaisesRegex(WorkerSessionError, "HTTP 402"):
            self.load(auth)
        self.assertEqual(len(auth.refresh_calls), 1)
        self.assertEqual(auth.password_calls, [])

        with self.assertRaisesRegex(WorkerSessionError, "retry paused"):
            self.load(auth)
        self.assertEqual(len(auth.refresh_calls), 1)
        self.assertEqual(auth.password_calls, [])

    def test_stale_cache_beyond_max_lifetime_is_not_trusted(self) -> None:
        """A tampered/edited cache must not pin a token forever."""
        auth = FakeAuth()
        self.load(auth)
        raw = json.loads(open(self.state, encoding="utf-8").read())
        raw["written_at"] = time.time() - 7200
        raw["expires_at"] = time.time() + 7200
        with open(self.state, "w", encoding="utf-8") as handle:
            json.dump(raw, handle)

        # The cache is not trusted at all, so the refresh token in it is not
        # reused either -- this falls back to a fresh password grant.
        session = self.load(auth)
        self.assertEqual(session.source, "password")
        self.assertEqual(auth.refresh_calls, [])

    def test_status_reports_absent_cache_without_secrets(self) -> None:
        status = session_status()
        self.assertFalse(status["present"])
        self.assertFalse(status["usable"])


class ConcurrentRefreshTests(unittest.TestCase):
    """Two processes on the same minute must not rotate the token twice."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.state = os.path.join(self._tmp.name, "worker-session.json")
        self.lock = os.path.join(self._tmp.name, "worker-session.lock")

    def test_parallel_loads_produce_one_grant(self) -> None:
        import threading

        auth = FakeAuth()
        results: list[WorkerSession] = []
        errors: list[BaseException] = []
        barrier = threading.Barrier(8)

        def worker() -> None:
            try:
                barrier.wait(timeout=10)
                results.append(
                    load_worker_session(
                        auth_factory=lambda: auth,
                        email="worker@example.com",
                        password="synthetic-password",
                        state_path=self.state,
                        lock_timeout=30,
                    )
                )
            except BaseException as exc:  # noqa: BLE001 - recorded for assertion
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)

        self.assertEqual(errors, [])
        self.assertEqual(len(results), 8)
        # One process signs in; the rest reuse the session it wrote.
        self.assertEqual(len(auth.password_calls), 1)
        self.assertEqual({r.access_token for r in results}, {"access-1"})


if __name__ == "__main__":
    unittest.main()
