from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from letter_registry.fingerprints import sha256_file


class FingerprintTests(unittest.TestCase):
    def test_same_content_has_same_fingerprint(self) -> None:
        with TemporaryDirectory() as directory:
            first = Path(directory) / "first.pdf"
            second = Path(directory) / "second.pdf"
            first.write_bytes(b"synthetic-document")
            second.write_bytes(b"synthetic-document")

            self.assertEqual(sha256_file(first), sha256_file(second))
