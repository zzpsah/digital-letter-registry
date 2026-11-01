"""Fixed-scope, aggregate-only Digital Letter Registry read model for VidyaDesk."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

SCHOOL_KEY = "umv-tetahali"
SCHOOL_NAME = "UCHCH MADHYAMIK VIDYALAY, TETAHALI"


def build_summary(
    *,
    public_document_count: int,
    latest_public_document_at: str | None,
    archive_name: str,
    expected_archive_name: str,
    school_key: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Validate the fixed archive identity and format an aggregate-only response."""
    if school_key != SCHOOL_KEY:
        raise ValueError("VidyaDesk school scope is not configured")
    if not expected_archive_name.strip() or archive_name.strip().casefold() != expected_archive_name.strip().casefold():
        raise ValueError("configured archive identity does not match the verified archive")
    count = int(public_document_count)
    if count < 0:
        raise ValueError("negative aggregate count")

    latest = None
    if latest_public_document_at:
        parsed = datetime.fromisoformat(str(latest_public_document_at).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        latest = parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    retrieved = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    retrieved_at = retrieved.isoformat().replace("+00:00", "Z")
    data = {
        "publicDocumentCount": count,
        "latestPublicDocumentAt": latest,
    }
    fingerprint = hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
    return {
        "contractVersion": "1.0.0",
        "sourceSystem": "digital-letter-registry",
        "scope": {
            "schoolKey": SCHOOL_KEY,
            "schoolName": SCHOOL_NAME,
        },
        "retrievedAt": retrieved_at,
        "snapshot": {
            "id": "dlr-vd-" + fingerprint,
            "version": 1,
            "createdAt": retrieved_at,
        },
        "data": data,
    }
