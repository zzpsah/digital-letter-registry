from datetime import datetime, timezone
import unittest

from letter_registry.channel_intake import (
    ChannelIntakeService,
    InboundAttachment,
    IntakeChannel,
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

    def save_source(self, *, owner_id, letter_id, attachment):
        self.rows.append((owner_id, letter_id, attachment))


class FakeTransport:
    def __init__(self):
        self.calls = []

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
                        channel=channel,
                        filename=f"synthetic-{channel.value}.pdf",
                        content=b"%PDF-synthetic",
                        received_at=datetime(
                            2026, 10, 2, tzinfo=timezone.utc
                        ),
                        external_message_id=f"msg-{channel.value}",
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

    def test_attachment_filename_must_be_basename(self):
        with self.assertRaises(ValueError):
            InboundAttachment(
                channel=IntakeChannel.EMAIL,
                filename="../synthetic.pdf",
                content=b"x",
            )

    def test_provenance_adapter_keeps_channel_metadata_private(self):
        transport = FakeTransport()
        repository = SupabaseProvenanceRepository(transport)
        attachment = InboundAttachment(
            channel=IntakeChannel.WHATSAPP,
            filename="synthetic-whatsapp.pdf",
            content=b"%PDF-synthetic",
            external_message_id="synthetic-message-id",
            source_label="synthetic-group",
            metadata={"forwarded": True},
        )

        repository.save_source(
            owner_id=OWNER_ID,
            letter_id="22222222-2222-4222-8222-222222222222",
            attachment=attachment,
        )

        table, row, conflict = transport.calls[0]
        self.assertEqual(table, "letter_sources")
        self.assertEqual(row["source_channel"], "whatsapp")
        self.assertEqual(row["metadata"], {"forwarded": True})
        self.assertEqual(
            conflict,
            "owner_id,source_channel,external_message_id",
        )

    def test_empty_attachment_is_rejected(self):
        with self.assertRaises(ValueError):
            InboundAttachment(
                channel=IntakeChannel.TELEGRAM,
                filename="synthetic.pdf",
                content=b"",
            )


if __name__ == "__main__":
    unittest.main()
