"""Runtime readiness checks without exposing secret values."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True, slots=True)
class ReadinessCheck:
    name: str
    ready: bool
    detail: str


@dataclass(frozen=True, slots=True)
class RuntimeReadiness:
    checks: tuple[ReadinessCheck, ...]

    @property
    def ready(self) -> bool:
        return all(check.ready for check in self.checks)

    def as_dict(self) -> dict[str, object]:
        return {
            "ready": self.ready,
            "checks": [
                {
                    "name": check.name,
                    "ready": check.ready,
                    "detail": check.detail,
                }
                for check in self.checks
            ],
        }


def _present(name: str) -> bool:
    return bool(os.environ.get(name, "").strip())


def _drive_credentials_ready() -> bool:
    credentials_file = os.environ.get("GOOGLE_OAUTH_CREDENTIALS_FILE", "").strip()
    if credentials_file and os.path.isfile(credentials_file):
        return True
    if _present("GOOGLE_DRIVE_ACCESS_TOKEN"):
        return True
    return all(
        _present(name)
        for name in (
            "GOOGLE_OAUTH_CLIENT_ID",
            "GOOGLE_OAUTH_CLIENT_SECRET",
            "GOOGLE_DRIVE_REFRESH_TOKEN",
        )
    )


def _auth_redirect_ready() -> bool:
    value = os.environ.get("AUTH_REDIRECT_URL", "").strip()
    if not value:
        return False
    parsed = urlsplit(value)
    if parsed.scheme == "https" and parsed.netloc:
        return parsed.path.rstrip("/") == "/auth/confirm"
    if (
        parsed.scheme == "http"
        and parsed.hostname in {"localhost", "127.0.0.1"}
        and parsed.netloc
    ):
        return parsed.path.rstrip("/") == "/auth/confirm"
    return False


def _runtime_executable(env_name: str, default: str) -> str | None:
    """Resolve an explicit runtime command before falling back to PATH."""

    configured = os.environ.get(env_name, "").strip()
    return shutil.which(configured or default)


def _ocr_languages(executable: str | None) -> set[str]:
    if not executable:
        return set()
    try:
        result = subprocess.run(
            [executable, "--list-langs"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return set()
    if result.returncode != 0:
        return set()
    return {
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip() and not line.lower().startswith("list of available")
    }


def check_runtime_readiness() -> RuntimeReadiness:
    """Check configuration/tool presence without returning secret values."""

    tesseract = _runtime_executable("TESSERACT_CMD", "tesseract")
    ocrmypdf = _runtime_executable("OCRMYPDF_CMD", "ocrmypdf")
    languages = _ocr_languages(tesseract)
    tesseract_ready = tesseract is not None
    ocrmypdf_ready = ocrmypdf is not None

    checks = (
        ReadinessCheck(
            "supabase_runtime",
            _present("SUPABASE_URL") and _present("SUPABASE_PUBLISHABLE_KEY"),
            "configured" if (
                _present("SUPABASE_URL")
                and _present("SUPABASE_PUBLISHABLE_KEY")
            ) else "missing required Supabase runtime values",
        ),
        ReadinessCheck(
            "auth_callback",
            _auth_redirect_ready(),
            "configured" if _auth_redirect_ready()
            else "AUTH_REDIRECT_URL must end in /auth/confirm on HTTPS or localhost",
        ),
        ReadinessCheck(
            "drive_credentials",
            _drive_credentials_ready(),
            "configured" if _drive_credentials_ready()
            else "missing Drive access token or OAuth refresh credentials",
        ),
        ReadinessCheck(
            "drive_originals_folder",
            _present("DRIVE_ORIGINALS_FOLDER_REFERENCE"),
            "configured" if _present("DRIVE_ORIGINALS_FOLDER_REFERENCE")
            else "missing private originals folder reference",
        ),
        ReadinessCheck(
            "gemini",
            _present("GEMINI_API_KEY"),
            "configured" if _present("GEMINI_API_KEY")
            else "missing Gemini runtime key",
        ),
        ReadinessCheck(
            "tesseract",
            tesseract_ready,
            "available" if tesseract_ready else "tesseract executable not found",
        ),
        ReadinessCheck(
            "ocrmypdf",
            ocrmypdf_ready,
            "available" if ocrmypdf_ready else "ocrmypdf executable not found",
        ),
        ReadinessCheck(
            "ocr_languages_hin_eng",
            {"hin", "eng"}.issubset(languages),
            "available" if {"hin", "eng"}.issubset(languages)
            else "Hindi and/or English Tesseract language data missing",
        ),
        ReadinessCheck(
            "synthetic_safety",
            os.environ.get("ENABLE_REAL_INTAKE", "").strip().lower()
            not in {"1", "true", "yes", "on"},
            "synthetic-only mode" if (
                os.environ.get("ENABLE_REAL_INTAKE", "").strip().lower()
                not in {"1", "true", "yes", "on"}
            ) else "real intake is enabled",
        ),
    )
    return RuntimeReadiness(checks=checks)
