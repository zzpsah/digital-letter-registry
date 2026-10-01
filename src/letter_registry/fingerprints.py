"""Content fingerprints used for duplicate detection."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

_CHUNK_SIZE = 1024 * 1024


def sha256_file(path: str | Path) -> str:
    """Return the stable SHA-256 fingerprint of a document without loading it all."""

    digest = sha256()
    with Path(path).open("rb") as document:
        for chunk in iter(lambda: document.read(_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()
