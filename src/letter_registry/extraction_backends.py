"""Concrete local extraction backends.

Native PDF text uses pypdf. OCR uses the external OCRmyPDF command and its
Tesseract language packs, supplied by the runtime environment.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory


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
        return "\n".join((page.extract_text() or "") for page in reader.pages)


@dataclass(slots=True)
class OcrmypdfTesseractBackend:
    """OCR PDFs with OCRmyPDF and read the generated sidecar text."""

    executable: str = field(default_factory=lambda: os.environ.get("OCRMY_PDF_CMD", "ocrmypdf"))
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
                "--sidecar",
                str(sidecar),
                "-l",
                language_arg,
                str(path),
                str(output_pdf),
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

            return sidecar.read_text(encoding="utf-8", errors="replace")



@dataclass(slots=True)
class TesseractImageBackend:
    """OCR JPG/JPEG/PNG images directly with Tesseract."""

    executable: str = field(default_factory=lambda: os.environ.get("TESSERACT_CMD", "tesseract"))
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
