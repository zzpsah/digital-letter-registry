import json
import unittest

from letter_registry.google_drive_renamer import GoogleDrivePrivateRenamer


class GoogleDrivePrivateRenamerTests(unittest.TestCase):
    def test_rename_uses_patch_and_keeps_object_reference_server_side(self):
        seen = {}

        def executor(req):
            seen["method"] = req.get_method()
            seen["url"] = req.full_url
            seen["authorization"] = req.headers["Authorization"]
            seen["body"] = json.loads(req.data.decode("utf-8"))
            return 200, '{"id":"synthetic-object","name":"new-name.pdf"}'

        renamer = GoogleDrivePrivateRenamer(
            access_token="synthetic-token",
            http_executor=executor,
        )
        renamer.rename(
            provider="gdrive",
            object_reference="synthetic-object",
            new_filename="new-name.pdf",
        )

        self.assertEqual(seen["method"], "PATCH")
        self.assertIn("/drive/v3/files/synthetic-object?", seen["url"])
        self.assertEqual(seen["authorization"], "Bearer synthetic-token")
        self.assertEqual(seen["body"], {"name": "new-name.pdf"})

    def test_path_like_target_filename_is_rejected(self):
        renamer = GoogleDrivePrivateRenamer(
            access_token="synthetic-token",
            http_executor=lambda req: (200, "{}"),
        )
        with self.assertRaises(ValueError):
            renamer.rename(
                provider="gdrive",
                object_reference="synthetic-object",
                new_filename="../unsafe.pdf",
            )

    def test_other_provider_is_rejected(self):
        renamer = GoogleDrivePrivateRenamer(
            access_token="synthetic-token",
            http_executor=lambda req: (200, "{}"),
        )
        with self.assertRaises(ValueError):
            renamer.rename(
                provider="s3",
                object_reference="synthetic-object",
                new_filename="safe.pdf",
            )


if __name__ == "__main__":
    unittest.main()
