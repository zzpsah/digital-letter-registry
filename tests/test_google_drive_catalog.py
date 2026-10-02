import json
import unittest

from letter_registry.google_drive_catalog import GoogleDrivePrivateCatalog


class GoogleDriveCatalogTests(unittest.TestCase):
    def test_catalog_lists_private_folder_metadata(self):
        seen = {}

        def executor(req):
            seen["url"] = req.full_url
            seen["authorization"] = req.headers["Authorization"]
            return 200, json.dumps({
                "files": [{
                    "id": "synthetic-drive-id",
                    "name": "synthetic-old-letter.pdf",
                    "mimeType": "application/pdf",
                    "size": "1234",
                    "modifiedTime": "2026-09-01T10:00:00Z",
                }]
            })

        catalog = GoogleDrivePrivateCatalog(
            access_token="synthetic-token",
            http_executor=executor,
        )
        rows = catalog.list_folder("synthetic-folder-id")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].filename, "synthetic-old-letter.pdf")
        self.assertEqual(rows[0].size_bytes, 1234)
        self.assertEqual(
            seen["authorization"],
            "Bearer synthetic-token",
        )
        self.assertIn("trashed", seen["url"])

    def test_folder_reference_rejects_path_like_value(self):
        catalog = GoogleDrivePrivateCatalog(
            access_token="synthetic-token",
            http_executor=lambda req: (200, '{"files":[]}'),
        )
        with self.assertRaises(ValueError):
            catalog.list_folder("../unsafe")


if __name__ == "__main__":
    unittest.main()
