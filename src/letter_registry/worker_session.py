"""Cross-process Supabase worker session reuse.

Background DLR services are short-lived `oneshot` units that each run once per
minute. Authenticating with `grant_type=password` on every start produced
thousands of password grants and tens of thousands of Supabase sessions per day
for a single worker identity.

This module keeps one worker session in a small on-disk cache so each run can
reuse a still-valid access token instead of signing in again, refreshing only
when the access token is close to expiring.

Concurrency: several timers fire on the same minute, so a refresh must never
race. The refresh token rotates on every use, so two processes refreshing at
once would invalidate each other's token. A single `flock`-protected lock
serialises the read-refresh-write cycle, and the lock is re-checked after
acquiring it so a process that lost the race reuses the winner's session
instead of refreshing again.

Nothing in here logs or returns credentials beyond the tokens the caller needs
for its own requests. Tokens are never written to stdout/stderr.
"""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator, Protocol


class _AuthLike(Protocol):
    """The subset of SupabasePasswordlessAuth this module needs."""

    def refresh_session(self, *, refresh_token: str) -> object: ...

    def sign_in_with_password(self, *, email: str, password: str) -> object: ...

DEFAULT_STATE_PATH = "/home/prashant/.hermes/state/dlr-auth/worker-session.json"
DEFAULT_LOCK_PATH = "/home/prashant/.hermes/state/dlr-auth/worker-session.lock"

# Refresh this many seconds before the access token actually expires. Supabase
# access tokens live an hour; the margin absorbs clock skew and slow runs.
DEFAULT_EXPIRY_MARGIN_SECONDS = 300

# An access token is only trusted for this long even if the server-reported
# expiry is further out, so a stale/edited cache cannot pin a dead token.
MAX_TOKEN_LIFETIME_SECONDS = 3600

_SESSION_FILE_MODE = 0o600
_DIR_MODE = 0o700


class WorkerSessionError(RuntimeError):
    """Raised when no usable worker session can be established."""


@dataclass(frozen=True, slots=True)
class WorkerSession:
    """A reusable worker session. Tokens are never logged by this module."""

    access_token: str
    refresh_token: str
    expires_at: float
    source: str  # "cache" | "refresh" | "password"

    def is_usable(self, *, margin: int = DEFAULT_EXPIRY_MARGIN_SECONDS) -> bool:
        return bool(self.access_token) and self.expires_at - margin > time.time()


def _state_paths(state_path: str | None) -> tuple[Path, Path]:
    path = Path(state_path or os.environ.get("DLR_WORKER_SESSION_FILE") or DEFAULT_STATE_PATH)
    lock = Path(os.environ.get("DLR_WORKER_SESSION_LOCK") or DEFAULT_LOCK_PATH)
    return path, lock


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=_DIR_MODE)
    try:
        os.chmod(path.parent, _DIR_MODE)
    except OSError:
        pass


@contextmanager
def _exclusive_lock(lock_path: Path, *, timeout: float = 30.0) -> Iterator[None]:
    """Serialise refresh-token rotation across processes.

    Blocks up to `timeout` seconds for the lock. Blocking (not failing fast) is
    deliberate: a losing process should wait briefly and then reuse the session
    the winner just wrote, rather than sign in with the password.
    """
    _ensure_parent(lock_path)
    handle = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, _SESSION_FILE_MODE)
    try:
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise WorkerSessionError(
                        "timed out waiting for the worker session lock"
                    )
                time.sleep(0.05)
        yield
    finally:
        try:
            fcntl.flock(handle, fcntl.LOCK_UN)
        finally:
            os.close(handle)


def _read_cached(path: Path) -> WorkerSession | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    if not isinstance(raw, dict):
        return None
    access = str(raw.get("access_token") or "").strip()
    refresh = str(raw.get("refresh_token") or "").strip()
    try:
        expires_at = float(raw.get("expires_at") or 0)
    except (TypeError, ValueError):
        return None
    written_at = float(raw.get("written_at") or expires_at)
    if not access or not refresh or expires_at <= 0:
        return None
    # Never trust a token claimed to be valid far beyond its real lifetime.
    if written_at + MAX_TOKEN_LIFETIME_SECONDS < time.time():
        return None
    return WorkerSession(
        access_token=access,
        refresh_token=refresh,
        expires_at=expires_at,
        source="cache",
    )


def _write_cached(path: Path, session: WorkerSession) -> None:
    """Persist atomically with 0600 so a partial write can never be read."""
    _ensure_parent(path)
    payload = {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "expires_at": session.expires_at,
        "written_at": time.time(),
        # Non-secret: lets operators see whether runs are reusing or refreshing.
        "obtained_via": session.source,
    }
    fd, temp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".worker-session-")
    try:
        os.fchmod(fd, _SESSION_FILE_MODE)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False)
        os.replace(temp_name, path)
        os.chmod(path, _SESSION_FILE_MODE)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _session_from_auth_result(result: object, *, source: str) -> WorkerSession:
    access = str(getattr(result, "access_token", "") or "").strip()
    refresh = str(getattr(result, "refresh_token", "") or "").strip()
    try:
        expires_in = int(getattr(result, "expires_in", 0) or 0)
    except (TypeError, ValueError):
        expires_in = 0
    if not access or not refresh or expires_in <= 0:
        raise WorkerSessionError("Supabase Auth returned an unusable worker session")
    return WorkerSession(
        access_token=access,
        refresh_token=refresh,
        expires_at=time.time() + expires_in,
        source=source,
    )


def _password_grant(auth: _AuthLike, *, email: str, password: str) -> object:
    """Perform the last-resort password grant with a definite failure type.

    Called at most once per run, so a bad credential or a Supabase outage fails
    the run clearly instead of turning into a retry storm.
    """
    try:
        return auth.sign_in_with_password(email=email, password=password)
    except WorkerSessionError:
        raise
    except Exception as exc:
        # Never include the password or any token in the message.
        raise WorkerSessionError(
            f"worker password sign-in failed: {type(exc).__name__}"
        ) from exc


def load_worker_session(
    *,
    auth_factory: Callable[[], _AuthLike] | None = None,
    email: str,
    password: str,
    state_path: str | None = None,
    lock_timeout: float = 30.0,
    refresh_only: bool = False,
) -> WorkerSession:
    """Return a usable worker session, signing in only when unavoidable.

    Order of preference: a cached access token that is still comfortably valid,
    then a refresh-token grant, then a password grant. The password grant is a
    last resort, not the per-run default.

    `refresh_only` is used by the health check: it never performs a password
    grant, so a cache problem can never turn into a password login.
    """
    path, lock = _state_paths(state_path)

    cached = _read_cached(path)
    if cached is not None and cached.is_usable():
        return cached

    with _exclusive_lock(lock, timeout=lock_timeout):
        # Another process may have refreshed while we waited for the lock.
        cached = _read_cached(path)
        if cached is not None and cached.is_usable():
            return cached

        auth = (auth_factory or _default_auth_factory)()
        refresh_token = cached.refresh_token if cached is not None else ""

        if refresh_token:
            try:
                refreshed = _session_from_auth_result(
                    auth.refresh_session(refresh_token=refresh_token),
                    source="refresh",
                )
                _write_cached(path, refreshed)
                return refreshed
            except Exception:
                # An expired or already-rotated refresh token is expected
                # occasionally; fall through to a password grant. The reason is
                # not logged with any token material.
                if refresh_only:
                    raise WorkerSessionError(
                        "worker session refresh failed and password sign-in is not "
                        "permitted for this caller"
                    )

        if refresh_only:
            raise WorkerSessionError(
                "no usable cached worker session and password sign-in is not "
                "permitted for this caller"
            )

        signed_in = _session_from_auth_result(
            _password_grant(auth, email=email, password=password),
            source="password",
        )
        # Record how this session was obtained without leaking any token value.
        _write_cached(
            path,
            WorkerSession(
                access_token=signed_in.access_token,
                refresh_token=signed_in.refresh_token,
                expires_at=signed_in.expires_at,
                source="password",
            ),
        )
        return signed_in


def _default_auth_factory() -> _AuthLike:
    from .auth import SupabasePasswordlessAuth

    return SupabasePasswordlessAuth.from_environment()


def session_status(*, state_path: str | None = None) -> dict[str, object]:
    """Non-secret view of the cached session, for health checks and diagnostics."""
    path, _ = _state_paths(state_path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError
    except (OSError, json.JSONDecodeError, ValueError):
        return {"present": False, "usable": False}

    try:
        expires_at = float(raw.get("expires_at") or 0)
    except (TypeError, ValueError):
        return {"present": False, "usable": False}

    now = time.time()
    return {
        "present": True,
        "usable": expires_at - DEFAULT_EXPIRY_MARGIN_SECONDS > now,
        "expires_in_seconds": int(expires_at - now),
        "has_refresh_token": bool(str(raw.get("refresh_token") or "").strip()),
        "obtained_via": str(raw.get("obtained_via") or "unknown"),
    }
