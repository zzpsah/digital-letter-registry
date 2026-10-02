"""Vercel entrypoint for the DLR control plane.

Vercel system environment variables determine the public origin dynamically.
Project-specific Supabase/archive settings remain runtime environment variables
and are never committed here.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

vercel_host = (
    os.environ.get("VERCEL_PROJECT_PRODUCTION_URL", "").strip()
    or os.environ.get("VERCEL_URL", "").strip()
)
if vercel_host:
    origin = vercel_host if vercel_host.startswith("http") else f"https://{vercel_host}"
    os.environ.setdefault("AUTH_APP_ORIGIN", origin)
    os.environ.setdefault("AUTH_REDIRECT_URL", f"{origin.rstrip('/')}/auth/confirm")
    os.environ.setdefault("AUTH_COOKIE_SECURE", "true")

from letter_registry.api import app  # noqa: E402
