"""Canonical current processing-version registry."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass

from .naming import FILENAME_RULE_VERSION
from .reprocessing import ReprocessingTargets


PDF_OCR_VERSION = "ocr-pdf-hi-en-v1"
IMAGE_OCR_VERSION = "ocr-image-hi-en-v1"
DICTIONARY_VERSION = "gov-education-hi-en-auto-v2"
CATEGORY_SCHEMA_VERSION = "education-letter-category-v1"
STATUS_RULE_VERSION = "relationships-v1"


@dataclass(frozen=True, slots=True)
class ProcessingVersionRegistry:
    extraction_native_pdf: str
    extraction_pdf_ocr: str
    extraction_image_ocr: str
    context_version: str
    dictionary_version: str
    filename_rule_version: str
    category_schema_version: str
    embedding_version: str
    status_rule_version: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    def reprocessing_targets(self) -> ReprocessingTargets:
        return ReprocessingTargets(
            ocr_version=self.extraction_pdf_ocr,
            context_version=self.context_version,
            dictionary_version=self.dictionary_version,
            filename_rule_version=self.filename_rule_version,
            category_schema_version=self.category_schema_version,
            embedding_version=self.embedding_version,
            status_rule_version=self.status_rule_version,
        )


def current_processing_versions() -> ProcessingVersionRegistry:
    ai_model = os.environ.get("AI_MODEL", "gemini-3.8-flash").strip()
    embedding_model = os.environ.get(
        "EMBEDDING_MODEL",
        "gemini-embedding-2",
    ).strip()
    dimensions = int(os.environ.get("EMBEDDING_DIMENSIONS", "768"))

    if not ai_model:
        raise ValueError("AI_MODEL cannot be empty")
    if not embedding_model:
        raise ValueError("EMBEDDING_MODEL cannot be empty")
    if dimensions < 128 or dimensions > 3072:
        raise ValueError("EMBEDDING_DIMENSIONS must be between 128 and 3072")

    return ProcessingVersionRegistry(
        extraction_native_pdf="native-pdf-v1",
        extraction_pdf_ocr=PDF_OCR_VERSION,
        extraction_image_ocr=IMAGE_OCR_VERSION,
        context_version=f"gemini:{ai_model}:context-v1",
        dictionary_version=DICTIONARY_VERSION,
        filename_rule_version=FILENAME_RULE_VERSION,
        category_schema_version=CATEGORY_SCHEMA_VERSION,
        embedding_version=f"gemini:{embedding_model}:{dimensions}:v1",
        status_rule_version=STATUS_RULE_VERSION,
    )
