import os
import unittest
from unittest.mock import patch

from letter_registry.google_drive_reader import GoogleDrivePrivateTransport


class GoogleDrivePrivateTransportTests(unittest.TestCase):
    def test_download_uses_bearer_token_and_returns_bytes(self):
        seen = {}

        def executor(req):
            seen["url"] = req.full_url
            seen["authorization"] = req.headers["Authorization"]
            return 200, b"%PDF-synthetic", "application/pdf"

        transport = GoogleDrivePrivateTransport(
            access_token="synthetic-token",
            http_executor=executor,
        )
        original = transport.download(
            provider="gdrive",
            object_reference="synthetic-object-id",
            filename="letter.pdf",
        )

        self.assertEqual(original.content, b"%PDF-synthetic")
        self.assertEqual(original.content_type, "application/pdf")
        self.assertIn("/drive/v3/files/synthetic-object-id?", seen["url"])
        self.assertEqual(seen["authorization"], "Bearer synthetic-token")

    def test_object_reference_rejects_path_like_input(self):
        transport = GoogleDrivePrivateTransport(
            access_token="synthetic-token",
            http_executor=lambda req: (200, b"", "application/pdf"),
        )
        with self.assertRaises(ValueError):
            transport.download(
                provider="gdrive",
                object_reference="../unsafe",
                filename="letter.pdf",
            )

    def test_other_provider_is_rejected(self):
        transport = GoogleDrivePrivateTransport(
            access_token="synthetic-token",
            http_executor=lambda req: (200, b"", None),
        )
        with self.assertRaises(ValueError):
            transport.download(
                provider="s3",
                object_reference="object",
                filename="letter.pdf",
            )

    def test_environment_requires_access_token(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                GoogleDrivePrivateTransport.from_environment()


if __name__ == "__main__":
    unittest.main()
