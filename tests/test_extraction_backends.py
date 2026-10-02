from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from letter_registry.extraction_backends import (
    OcrmypdfTesseractBackend,
    TesseractImageBackend,
)


class OcrmypdfBackendTests(unittest.TestCase):
    def test_languages_are_joined_for_tesseract(self) -> None:
        with TemporaryDirectory() as directory:
            source = Path(directory) / "synthetic.pdf"
            source.write_bytes(b"%PDF-synthetic")

            def fake_run(command, **kwargs):
                sidecar_index = command.index("--sidecar") + 1
                Path(command[sidecar_index]).write_text(
                    "शिक्षा विभाग synthetic OCR text",
                    encoding="utf-8",
                )

                class Result:
                    returncode = 0
                    stderr = ""
                    stdout = ""

                self.assertIn("hin+eng", command)
                return Result()

            backend = OcrmypdfTesseractBackend()

            with patch("subprocess.run", side_effect=fake_run):
                text = backend.extract_text(source, languages=("hin", "eng"))

            self.assertIn("शिक्षा विभाग", text)

    def test_missing_executable_is_reported_cleanly(self) -> None:
        with TemporaryDirectory() as directory:
            source = Path(directory) / "synthetic.pdf"
            source.write_bytes(b"%PDF-synthetic")
            backend = OcrmypdfTesseractBackend(executable="missing-ocrmypdf")

            with patch("subprocess.run", side_effect=FileNotFoundError):
                with self.assertRaisesRegex(RuntimeError, "OCRmyPDF executable"):
                    backend.extract_text(source, languages=("hin", "eng"))

    def test_empty_languages_are_rejected(self) -> None:
        backend = OcrmypdfTesseractBackend()
        with self.assertRaises(ValueError):
            backend.extract_text(Path("synthetic.pdf"), languages=())


if __name__ == "__main__":
    unittest.main()



class TesseractImageBackendTests(unittest.TestCase):
    def test_image_backend_uses_hindi_and_english(self) -> None:
        seen = {}

        def fake_run(command, **kwargs):
            seen["command"] = command

            class Result:
                returncode = 0
                stderr = ""
                stdout = "शिक्षा विभाग synthetic image text"

            return Result()

        backend = TesseractImageBackend()
        with patch("subprocess.run", side_effect=fake_run):
            text = backend.extract_text(
                Path("synthetic.jpg"),
                languages=("hin", "eng"),
            )

        self.assertIn("शिक्षा विभाग", text)
        self.assertIn("hin+eng", seen["command"])


