from datetime import datetime, timezone
import unittest

from letter_registry.channel_intake import (
    ChannelIntakeService,
    InboundAttachment,
    IntakeChannel,
    IntakeProvenance,
    SupabaseProvenanceRepository,
)
from letter_registry.intake import IntakeService
from letter_registry.jobs import InMemoryProcessingQueue
from letter_registry.persistence import InMemoryLetterRepository
from letter_registry.storage import InMemoryOriginalStorage


OWNER_ID = "11111111-1111-4111-8111-111111111111"


class FakeProvenance:
    def __init__(self):
        self.rows = []

    def save_source(self, *, owner_id, letter_id, provenance):
        self.rows.append((owner_id, letter_id, provenance))


class FakeTransport:
    def __init__(self):
        self.calls = []

    def select(self, table, *, filters=None, columns="*"):
        return []

    def insert(self, table, row, *, on_conflict=None):
        self.calls.append((table, row, on_conflict))
        return row


class ChannelIntakeTests(unittest.TestCase):
    def service(self):
        provenance = FakeProvenance()
        service = ChannelIntakeService(
            intake=IntakeService(
                storage=InMemoryOriginalStorage(),
                repository=InMemoryLetterRepository(),
                queue=InMemoryProcessingQueue(),
            ),
            provenance=provenance,
        )
        return service, provenance

    def test_each_supported_channel_uses_same_intake_pipeline(self):
        for channel in (
            IntakeChannel.TELEGRAM,
            IntakeChannel.WHATSAPP,
            IntakeChannel.EMAIL,
            IntakeChannel.WATCHED_FOLDER,
        ):
            with self.subTest(channel=channel):
                service, provenance = self.service()
                result = service.ingest(
                    InboundAttachment(
                        provenance=IntakeProvenance(
                            channel=channel,
                            filename=f"synthetic-{channel.value}.pdf",
                            received_at=datetime(
                                2026, 10, 2, tzinfo=timezone.utc
                            ),
                            external_message_id=f"msg-{channel.value}",
                        ),
                        content=b"%PDF-synthetic",
                    ),
                    owner_id=OWNER_ID,
                )

                self.assertEqual(
                    provenance.rows[0][1],
                    result.record.record_id,
                )
                self.assertEqual(
                    provenance.rows[0][2].channel,
                    channel,
                )

    def test_provenance_filename_must_be_basename(self):
        with self.assertRaises(ValueError):
            IntakeProvenance(
                channel=IntakeChannel.EMAIL,
                filename="../synthetic.pdf",
            )

    def test_provenance_adapter_keeps_channel_metadata_private(self):
        transport = FakeTransport()
        repository = SupabaseProvenanceRepository(transport)
        provenance = IntakeProvenance(
            channel=IntakeChannel.WHATSAPP,
            filename="synthetic-whatsapp.pdf",
            external_message_id="synthetic-message-id",
            source_label="synthetic-group",
            metadata={"forwarded": True},
        )

        repository.save_source(
            owner_id=OWNER_ID,
            letter_id="22222222-2222-4222-8222-222222222222",
            provenance=provenance,
        )

        table, row, conflict = transport.calls[0]
        self.assertEqual(table, "letter_sources")
        self.assertEqual(row["source_channel"], "whatsapp")
        self.assertEqual(row["metadata"], {"forwarded": True})
        self.assertIsNone(conflict)

    def test_empty_attachment_is_rejected(self):
        with self.assertRaises(ValueError):
            InboundAttachment(
                provenance=IntakeProvenance(
                    channel=IntakeChannel.TELEGRAM,
                    filename="synthetic.pdf",
                ),
                content=b"",
            )

    def test_ingest_path_requires_matching_provenance_filename(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory

        service, _ = self.service()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.pdf"
            path.write_bytes(b"%PDF-synthetic")
            with self.assertRaisesRegex(ValueError, "filename"):
                service.ingest_path(
                    path,
                    owner_id=OWNER_ID,
                    provenance=IntakeProvenance(
                        channel=IntakeChannel.WEB,
                        filename="other.pdf",
                    ),
                )


if __name__ == "__main__":
    unittest.main()
