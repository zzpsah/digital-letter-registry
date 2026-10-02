from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from letter_registry.intake_channels import (
    IntakeChannelAdapter,
    email_attachment,
    safe_attachment_filename,
    telegram_attachment,
    watched_folder_attachment,
    whatsapp_attachment,
)


OWNER_ID = "11111111-1111-4111-8111-111111111111"


class FakeIntake:
    def __init__(self):
        self.calls = []

    def ingest(self, path, *, owner_id):
        self.calls.append((Path(path).name, owner_id))
        return object()


class IntakeChannelTests(unittest.TestCase):
    def test_channel_helpers_preserve_only_safe_provenance(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-letter.pdf"
            path.write_bytes(b"%PDF")

            email = email_attachment(
                path,
                message_id="synthetic-email-message",
                sender="department@example.invalid",
            )
            telegram = telegram_attachment(
                path,
                file_id="synthetic-telegram-file",
                chat_label="Synthetic EDU",
            )
            whatsapp = whatsapp_attachment(
                path,
                message_id="synthetic-wa-message",
                chat_label="Synthetic EDU",
            )
            watched = watched_folder_attachment(path)

        self.assertEqual(email.provenance.channel, "email")
        self.assertEqual(telegram.provenance.channel, "telegram")
        self.assertEqual(whatsapp.provenance.channel, "whatsapp")
        self.assertEqual(watched.provenance.channel, "watched_folder")

    def test_adapter_delegates_to_canonical_intake(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-letter.pdf"
            path.write_bytes(b"%PDF")
            attachment = telegram_attachment(
                path,
                file_id="synthetic-file-id",
            )
            intake = FakeIntake()
            adapter = IntakeChannelAdapter(intake)

            result = adapter.submit(
                attachment,
                owner_id=OWNER_ID,
            )

        self.assertEqual(
            intake.calls,
            [("synthetic-letter.pdf", OWNER_ID)],
        )
        self.assertEqual(result.provenance.channel, "telegram")

    def test_filename_normalization_rejects_path_traversal(self):
        self.assertEqual(
            safe_attachment_filename("../../synthetic letter.pdf"),
            "synthetic letter.pdf",
        )

    def test_staged_filename_must_match_normalized_name(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "wrong-name.pdf"
            path.write_bytes(b"%PDF")
            attachment = telegram_attachment(
                path,
                file_id="synthetic-file-id",
            )
            object.__setattr__(
                attachment,
                "filename",
                "different-name.pdf",
            )

            with self.assertRaisesRegex(ValueError, "must match"):
                IntakeChannelAdapter(FakeIntake()).submit(
                    attachment,
                    owner_id=OWNER_ID,
                )


if __name__ == "__main__":
    unittest.main()
