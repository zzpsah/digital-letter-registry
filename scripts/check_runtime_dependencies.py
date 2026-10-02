"""Check optional runtime dependencies without exposing secrets."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys


def _command_version(command: str, *args: str) -> str | None:
    path = shutil.which(command)
    if not path:
        return None
    result = subprocess.run(
        [path, *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    text = (result.stdout or result.stderr).strip()
    return text.splitlines()[0] if text else "available"


def _tesseract_languages() -> list[str]:
    path = shutil.which("tesseract")
    if not path:
        return []
    result = subprocess.run(
        [path, "--list-langs"],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip() and not line.lower().startswith("list of available")
    ]


def runtime_report() -> dict[str, object]:
    languages = _tesseract_languages()
    return {
        "python": sys.version.split()[0],
        "tesseract": _command_version("tesseract", "--version"),
        "ocrmypdf": _command_version("ocrmypdf", "--version"),
        "tesseract_languages": languages,
        "ocr_ready": bool(
            shutil.which("tesseract")
            and shutil.which("ocrmypdf")
            and "hin" in languages
            and "eng" in languages
        ),
    }


def main() -> int:
    report = runtime_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ocr_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
