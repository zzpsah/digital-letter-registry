import unittest
from unittest.mock import patch, Mock

from scripts.check_runtime_dependencies import runtime_report


class RuntimeDependencyCheckTests(unittest.TestCase):
    @patch("scripts.check_runtime_dependencies.subprocess.run")
    @patch("scripts.check_runtime_dependencies.shutil.which")
    def test_ocr_ready_when_binaries_and_languages_exist(self, which, run):
        which.side_effect = lambda name: f"/usr/bin/{name}"
        version = Mock(stdout="5.3.4\n", stderr="")
        langs = Mock(stdout="List of available languages (2):\neng\nhin\n", stderr="")
        run.side_effect = [langs, version, version]

        report = runtime_report()

        self.assertTrue(report["ocr_ready"])
        self.assertIn("hin", report["tesseract_languages"])
        self.assertIn("eng", report["tesseract_languages"])

    @patch("scripts.check_runtime_dependencies.subprocess.run")
    @patch("scripts.check_runtime_dependencies.shutil.which")
    def test_ocr_not_ready_when_binaries_missing(self, which, run):
        which.return_value = None

        report = runtime_report()

        self.assertFalse(report["ocr_ready"])
        self.assertIsNone(report["tesseract"])
        self.assertIsNone(report["ocrmypdf"])
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
