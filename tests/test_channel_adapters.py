from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from letter_registry.channel_adapters import (
    email_attachment,
    telegram_attachment,
    watched_file_attachment,
    whatsapp_attachment,
)
from letter_registry.channel_intake import IntakeChannel


class ChannelAdapterTests(unittest.TestCase):
    def test_message_channels_preserve_message_ids(self):
        cases = [
            (
                telegram_attachment,
                IntakeChannel.TELEGRAM,
                {"chat_label": "synthetic-chat"},
            ),
            (
                whatsapp_attachment,
                IntakeChannel.WHATSAPP,
                {"chat_label": "synthetic-group"},
            ),
            (
                email_attachment,
                IntakeChannel.EMAIL,
                {"sender_label": "synthetic-sender"},
            ),
        ]
        for factory, channel, extra in cases:
            with self.subTest(channel=channel):
                attachment = factory(
                    filename="synthetic-letter.pdf",
                    content=b"%PDF-synthetic",
                    message_id="synthetic-message-id",
                    **extra,
                )
                self.assertEqual(attachment.channel, channel)
                self.assertEqual(
                    attachment.provenance.external_message_id,
                    "synthetic-message-id",
                )

    def test_provider_path_is_reduced_to_basename(self):
        attachment = telegram_attachment(
            filename="/tmp/provider/synthetic.pdf",
            content=b"x",
            message_id="msg",
        )
        self.assertEqual(attachment.filename, "synthetic.pdf")

    def test_watched_folder_reads_existing_file(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-watch.pdf"
            path.write_bytes(b"%PDF-watch")

            attachment = watched_file_attachment(
                path,
                source_label="synthetic-watch-folder",
            )

        self.assertEqual(
            attachment.channel,
            IntakeChannel.WATCHED_FOLDER,
        )
        self.assertEqual(attachment.content, b"%PDF-watch")

    def test_watched_folder_rejects_missing_file(self):
        with self.assertRaises(ValueError):
            watched_file_attachment("/missing/synthetic.pdf")


if __name__ == "__main__":
    unittest.main()
