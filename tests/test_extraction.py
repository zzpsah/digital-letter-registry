from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from letter_registry.extraction import (
    VersionedTextExtractor,
    is_usable_native_text,
    normalize_extracted_text,
)


class FakePdfBackend:
    def __init__(self, text: str) -> None:
        self.text = text

    def extract_text(self, path: Path) -> str:
        return self.text


class FakeOcrBackend:
    def __init__(self, text: str) -> None:
        self.text = text
        self.languages = None

    def extract_text(self, path: Path, *, languages: tuple[str, ...]) -> str:
        self.languages = languages
        return self.text


class ExtractionTests(unittest.TestCase):
    def _file(self, directory: str) -> Path:
        path = Path(directory) / "synthetic.pdf"
        path.write_bytes(b"%PDF-synthetic")
        return path

    def test_normalization_preserves_hindi_unicode(self) -> None:
        self.assertEqual(
            normalize_extracted_text("  शिक्षा   विभाग \r\n\n अंतिम   तिथि  "),
            "शिक्षा विभाग\nअंतिम तिथि",
        )

    def test_native_text_is_used_when_meaningful(self) -> None:
        text = (
            "Education Department official circular regarding Intermediate "
            "registration and examination form deadline extension. "
            "आवश्यक कार्रवाई विद्यालय स्तर पर सुनिश्चित करें।"
        )
        with TemporaryDirectory() as directory:
            extractor = VersionedTextExtractor(FakePdfBackend(text))
            result = extractor.extract(self._file(directory))

        self.assertEqual(result.method, "native_pdf")
        self.assertFalse(result.needs_ocr)
        self.assertIn("आवश्यक कार्रवाई", result.text)

    def test_short_native_text_requests_ocr_when_backend_missing(self) -> None:
        with TemporaryDirectory() as directory:
            extractor = VersionedTextExtractor(FakePdfBackend("scan"))
            result = extractor.extract(self._file(directory))

        self.assertEqual(result.method, "native_pdf_insufficient")
        self.assertTrue(result.needs_ocr)

    def test_ocr_fallback_uses_hindi_and_english(self) -> None:
        ocr = FakeOcrBackend("बिहार विद्यालय परीक्षा समिति परीक्षा प्रपत्र अंतिम तिथि विस्तारित")
        with TemporaryDirectory() as directory:
            extractor = VersionedTextExtractor(
                FakePdfBackend(""),
                ocr_backend=ocr,
            )
            result = extractor.extract(self._file(directory))

        self.assertEqual(result.method, "ocr_pdf")
        self.assertEqual(result.version, "ocr-pdf-hi-en-v1")
        self.assertEqual(ocr.languages, ("hin", "eng"))
        self.assertFalse(result.needs_ocr)

    def test_image_uses_dedicated_ocr_backend(self) -> None:
        image_ocr = FakeOcrBackend("छात्रवृत्ति आवेदन अंतिम तिथि")
        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.jpg"
            path.write_bytes(b"synthetic-image")
            extractor = VersionedTextExtractor(
                FakePdfBackend("must-not-be-used"),
                image_ocr_backend=image_ocr,
            )
            result = extractor.extract(path)

        self.assertEqual(result.method, "ocr_image")
        self.assertEqual(result.version, "ocr-image-hi-en-v1")
        self.assertEqual(image_ocr.languages, ("hin", "eng"))
        self.assertIn("छात्रवृत्ति", result.text)

    def test_image_without_backend_requests_ocr(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.png"
            path.write_bytes(b"synthetic-image")
            result = VersionedTextExtractor(
                FakePdfBackend("unused")
            ).extract(path)

        self.assertTrue(result.needs_ocr)
        self.assertEqual(result.method, "image_ocr_unavailable")

    def test_usability_rejects_symbol_noise(self) -> None:
        self.assertFalse(is_usable_native_text("### --- ... " * 20))


if __name__ == "__main__":
    unittest.main()
