"""Concrete local extraction backends.

Native PDF text uses pypdf. OCR uses the external OCRmyPDF command and its
Tesseract language packs, supplied by the runtime environment.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory


def _resolve_command(env_name: str, command: str) -> str:
    """Resolve a runtime command from config, PATH, or the active Python venv."""
    configured = os.environ.get(env_name, "").strip()
    if configured:
        return str(Path(configured).expanduser())

    discovered = shutil.which(command)
    if discovered:
        return discovered

    # The worker runs with the project virtualenv Python. Console scripts such
    # as ocrmypdf therefore live next to sys.executable even when that venv's
    # bin directory is not exported into PATH by systemd/secret wrappers.
    sibling = Path(sys.executable).with_name(command)
    if sibling.is_file():
        return str(sibling)

    return command


@dataclass(slots=True)
class PypdfTextBackend:
    """Extract embedded/native PDF text with pypdf."""

    def extract_text(self, path: Path) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError(
                "pypdf is required for native PDF extraction; install project dependencies"
            ) from exc

        reader = PdfReader(str(path))
        parts: list[str] = []
        for page_number, page in enumerate(reader.pages, start=1):
            parts.append(f"[[PAGE {page_number}]]\n{page.extract_text() or ''}")
        return "\n".join(parts)


@dataclass(slots=True)
class OcrmypdfTesseractBackend:
    """OCR PDFs with OCRmyPDF and read the generated sidecar text."""

    executable: str = field(default_factory=lambda: _resolve_command("OCRMY_PDF_CMD", "ocrmypdf"))
    timeout_seconds: int = 180

    def extract_text(self, path: Path, *, languages: tuple[str, ...]) -> str:
        if not languages:
            raise ValueError("at least one OCR language is required")

        language_arg = "+".join(languages)
        with TemporaryDirectory() as directory:
            workdir = Path(directory)
            sidecar = workdir / "sidecar.txt"
            output_pdf = workdir / "ocr-output.pdf"

            command = [
                self.executable,
                "--force-ocr",
                "--rotate-pages",
                "--deskew",
            ]
            # --clean depends on the optional 'unpaper' binary. OCR itself
            # remains fully functional without it, so do not make a missing
            # cosmetic helper a production blocker.
            if shutil.which("unpaper"):
                command.append("--clean")
            command.extend(
                [
                    "--optimize", "1",
                    "--sidecar",
                    str(sidecar),
                    "-l",
                    language_arg,
                    str(path),
                    str(output_pdf),
                ]
            )

            child_env = os.environ.copy()
            tesseract_cmd = child_env.get("TESSERACT_CMD", "").strip()
            if tesseract_cmd:
                tesseract_dir = str(Path(tesseract_cmd).expanduser().parent)
                child_env["PATH"] = (
                    tesseract_dir
                    + os.pathsep
                    + child_env.get("PATH", "")
                )

            try:
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    check=False,
                    env=child_env,
                )
            except FileNotFoundError as exc:
                raise RuntimeError(
                    "OCRmyPDF executable was not found; install OCRmyPDF/Tesseract at runtime"
                ) from exc
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError("OCRmyPDF timed out") from exc

            if completed.returncode != 0:
                detail = (completed.stderr or completed.stdout or "").strip()
                raise RuntimeError(
                    f"OCRmyPDF failed with exit code {completed.returncode}: {detail}"
                )

            if not sidecar.exists():
                raise RuntimeError("OCRmyPDF completed without producing sidecar text")

            raw = sidecar.read_text(encoding="utf-8", errors="replace")
            # OCRmyPDF sidecars normally separate pages with form-feed.
            # Preserve those boundaries so downstream analysis can cite pages.
            if "\f" in raw:
                pages = raw.split("\f")
                return "\n".join(
                    f"[[PAGE {page_number}]]\n{page_text}"
                    for page_number, page_text in enumerate(pages, start=1)
                    if page_text.strip()
                )
            return raw



@dataclass(slots=True)
class TesseractImageBackend:
    """OCR JPG/JPEG/PNG images directly with Tesseract."""

    executable: str = field(default_factory=lambda: _resolve_command("TESSERACT_CMD", "tesseract"))
    timeout_seconds: int = 120

    def extract_text(self, path: Path, *, languages: tuple[str, ...]) -> str:
        if not languages:
            raise ValueError("at least one OCR language is required")

        command = [
            self.executable,
            str(path),
            "stdout",
            "-l",
            "+".join(languages),
            "--psm",
            "6",
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                "Tesseract executable was not found"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Tesseract image OCR timed out") from exc

        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise RuntimeError(
                f"Tesseract image OCR failed with exit code "
                f"{completed.returncode}: {detail}"
            )
        return completed.stdout
