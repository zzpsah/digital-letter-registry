"""Versioned text-extraction contracts for official letters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    text: str
    method: str
    version: str
    needs_ocr: bool


class PdfTextBackend(Protocol):
    """Provider-neutral native PDF text reader."""

    def extract_text(self, path: Path) -> str:
        ...


class OcrBackend(Protocol):
    """Provider-neutral OCR reader used only when native text is insufficient."""

    def extract_text(self, path: Path, *, languages: tuple[str, ...]) -> str:
        ...


def normalize_extracted_text(text: str) -> str:
    """Normalize line endings/spacing without destroying Hindi Unicode text."""

    lines = [" ".join(line.split()) for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(line for line in lines if line).strip()


def is_usable_native_text(
    text: str,
    *,
    minimum_characters: int = 80,
    minimum_alphanumeric_ratio: float = 0.35,
) -> bool:
    """Heuristic: enough meaningful native text to skip OCR."""

    normalized = normalize_extracted_text(text)
    if len(normalized) < minimum_characters:
        return False

    meaningful = sum(1 for char in normalized if char.isalnum())
    ratio = meaningful / max(len(normalized), 1)
    return ratio >= minimum_alphanumeric_ratio


@dataclass(slots=True)
class VersionedTextExtractor:
    """Prefer native PDF text, then optionally fall back to OCR."""

    pdf_backend: PdfTextBackend
    ocr_backend: OcrBackend | None = None
    native_version: str = "native-pdf-v1"
    ocr_version: str = "ocr-hi-en-v1"
    ocr_languages: tuple[str, ...] = ("hin", "eng")

    def extract(self, path: str | Path) -> ExtractionResult:
        source = Path(path)
        if not source.is_file():
            raise ValueError("source path must be an existing file")

        native = normalize_extracted_text(self.pdf_backend.extract_text(source))
        if is_usable_native_text(native):
            return ExtractionResult(
                text=native,
                method="native_pdf",
                version=self.native_version,
                needs_ocr=False,
            )

        if self.ocr_backend is None:
            return ExtractionResult(
                text=native,
                method="native_pdf_insufficient",
                version=self.native_version,
                needs_ocr=True,
            )

        ocr_text = normalize_extracted_text(
            self.ocr_backend.extract_text(
                source,
                languages=self.ocr_languages,
            )
        )
        return ExtractionResult(
            text=ocr_text,
            method="ocr",
            version=self.ocr_version,
            needs_ocr=False,
        )
