"""Versioned text-extraction contracts for official letters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
import unicodedata


_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


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
    """Provider-neutral OCR reader."""

    def extract_text(self, path: Path, *, languages: tuple[str, ...]) -> str:
        ...


def normalize_extracted_text(text: str) -> str:
    """Normalize line endings/spacing without destroying Hindi Unicode text."""

    lines = [
        " ".join(line.split())
        for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    ]
    return "\n".join(line for line in lines if line).strip()


def is_usable_native_text(
    text: str,
    *,
    minimum_characters: int = 80,
    minimum_alphanumeric_ratio: float = 0.35,
    maximum_private_use_ratio: float = 0.01,
    maximum_replacement_ratio: float = 0.005,
) -> bool:
    """Heuristic: enough meaningful, correctly encoded native text to skip OCR."""

    normalized = normalize_extracted_text(text)
    if len(normalized) < minimum_characters:
        return False

    length = max(len(normalized), 1)
    meaningful = sum(1 for char in normalized if char.isalnum())
    if meaningful / length < minimum_alphanumeric_ratio:
        return False

    private_use = sum(
        1 for char in normalized if unicodedata.category(char) == "Co"
    )
    if private_use / length > maximum_private_use_ratio:
        return False

    replacement = normalized.count("�")
    if replacement / length > maximum_replacement_ratio:
        return False

    return True


@dataclass(slots=True)
class VersionedTextExtractor:
    """Prefer native PDF text; OCR PDFs/images only when required."""

    pdf_backend: PdfTextBackend
    ocr_backend: OcrBackend | None = None
    image_ocr_backend: OcrBackend | None = None
    native_version: str = "native-pdf-v1"
    ocr_version: str = "ocr-pdf-hi-en-v1"
    image_ocr_version: str = "ocr-image-hi-en-v1"
    ocr_languages: tuple[str, ...] = ("hin", "eng")

    def extract(self, path: str | Path) -> ExtractionResult:
        source = Path(path)
        if not source.is_file():
            raise ValueError("source path must be an existing file")

        suffix = source.suffix.lower()
        if suffix in _IMAGE_EXTENSIONS:
            if self.image_ocr_backend is None:
                return ExtractionResult(
                    text="",
                    method="image_ocr_unavailable",
                    version=self.image_ocr_version,
                    needs_ocr=True,
                )
            text = normalize_extracted_text(
                self.image_ocr_backend.extract_text(
                    source,
                    languages=self.ocr_languages,
                )
            )
            return ExtractionResult(
                text=text,
                method="ocr_image",
                version=self.image_ocr_version,
                needs_ocr=False,
            )

        if suffix != ".pdf":
            raise ValueError("unsupported extraction file type")

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
            method="ocr_pdf",
            version=self.ocr_version,
            needs_ocr=False,
        )
