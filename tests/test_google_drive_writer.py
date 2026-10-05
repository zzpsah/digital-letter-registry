import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from letter_registry.google_drive_writer import GoogleDrivePrivateWriter


class GoogleDrivePrivateWriterTests(unittest.TestCase):
    def test_upload_uses_private_folder_and_returns_object_id(self):
        seen = {}

        def executor(req):
            seen["url"] = req.full_url
            seen["authorization"] = req.headers["Authorization"]
            seen["content_type"] = req.headers["Content-type"]
            seen["body"] = req.data
            return 200, json.dumps({"id": "synthetic-drive-object"})

        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-letter.pdf"
            path.write_bytes(b"%PDF-synthetic")
            writer = GoogleDrivePrivateWriter(
                access_token="synthetic-token",
                http_executor=executor,
            )

            object_id = writer.upload_file(
                folder_reference="synthetic-folder-id",
                filename=path.name,
                path=path,
            )

        self.assertEqual(object_id, "synthetic-drive-object")
        self.assertIn("uploadType=multipart", seen["url"])
        self.assertEqual(seen["authorization"], "Bearer synthetic-token")
        self.assertIn("multipart/related", seen["content_type"])
        self.assertIn(b"synthetic-folder-id", seen["body"])
        self.assertIn(b"%PDF-synthetic", seen["body"])

    def test_replace_updates_existing_drive_object_in_place(self):
        seen = {}

        def executor(req):
            seen["method"] = req.method
            seen["url"] = req.full_url
            seen["authorization"] = req.headers["Authorization"]
            seen["content_type"] = req.headers["Content-type"]
            seen["body"] = req.data
            return 200, json.dumps({"id": "existing-drive-object"})

        with TemporaryDirectory() as directory:
            path = Path(directory) / "replacement.pdf"
            path.write_bytes(b"%PDF-replacement")
            writer = GoogleDrivePrivateWriter(
                access_token="synthetic-token",
                http_executor=executor,
            )
            object_id = writer.replace_file(
                object_reference="existing-drive-object",
                path=path,
            )

        self.assertEqual(object_id, "existing-drive-object")
        self.assertEqual(seen["method"], "PATCH")
        self.assertIn("/files/existing-drive-object", seen["url"])
        self.assertIn("uploadType=media", seen["url"])
        self.assertEqual(seen["authorization"], "Bearer synthetic-token")
        self.assertEqual(seen["body"], b"%PDF-replacement")

    def test_path_like_folder_reference_is_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.pdf"
            path.write_bytes(b"x")
            writer = GoogleDrivePrivateWriter(
                access_token="synthetic-token",
                http_executor=lambda req: (200, '{"id":"x"}'),
            )
            with self.assertRaises(ValueError):
                writer.upload_file(
                    folder_reference="../unsafe",
                    filename=path.name,
                    path=path,
                )


if __name__ == "__main__":
    unittest.main()
