from datetime import datetime, timezone
import unittest

from letter_registry.models import DocumentRecord
from letter_registry.supabase_repository import SupabaseLetterRepository


OWNER_ID = "11111111-1111-4111-8111-111111111111"
LETTER_ID = "22222222-2222-4222-8222-222222222222"


class FakeTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, object], str | None]] = []

    def insert(
        self,
        table: str,
        row: dict[str, object],
        *,
        on_conflict: str | None = None,
    ) -> dict[str, object]:
        self.calls.append(("insert", table, row, on_conflict))
        return row

    def upsert(
        self,
        table: str,
        row: dict[str, object],
        *,
        on_conflict: str,
    ) -> dict[str, object]:
        self.calls.append(("upsert", table, row, on_conflict))
        return row

    def update(
        self,
        table: str,
        row: dict[str, object],
        *,
        filters: dict[str, str],
    ) -> dict[str, object]:
        self.calls.append(("update", table, row, str(filters)))
        return row


def record() -> DocumentRecord:
    return DocumentRecord(
        record_id=LETTER_ID,
        original_filename="synthetic.pdf",
        original_sha256="a" * 64,
        original_storage_reference="synthetic-private-object",
        received_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
    )


class SupabaseRepositoryTests(unittest.TestCase):
    def test_rename_identity_lookup_stays_server_side(self) -> None:
        class IdentityTransport(FakeTransport):
            def select(self, table, *, filters=None, columns="*"):
                return [{
                    "id": LETTER_ID,
                    "original_filename": "DOC10086.pdf",
                    "storage_provider": "gdrive",
                    "storage_object_id": "private-object-reference",
                }]

        repository = SupabaseLetterRepository(IdentityTransport())
        identity = repository.get_rename_identity(LETTER_ID)

        self.assertEqual(identity.record_id, LETTER_ID)
        self.assertEqual(identity.original_filename, "DOC10086.pdf")
        self.assertEqual(identity.storage_provider, "gdrive")
        self.assertEqual(
            identity.storage_object_reference,
            "private-object-reference",
        )

    def test_source_insert_targets_letters_with_duplicate_conflict_key(self) -> None:
        transport = FakeTransport()
        repository = SupabaseLetterRepository(transport)

        repository.save_source(record(), owner_id=OWNER_ID)

        method, table, row, conflict = transport.calls[0]
        self.assertEqual(method, "insert")
        self.assertEqual(table, "letters")
        self.assertEqual(conflict, "owner_id,original_sha256")
        self.assertEqual(row["owner_id"], OWNER_ID)
        self.assertEqual(row["storage_provider"], "gdrive")

    def test_processing_state_is_upserted_by_letter_id(self) -> None:
        transport = FakeTransport()
        repository = SupabaseLetterRepository(transport)

        repository.save_processing_state(record(), owner_id=OWNER_ID)

        method, table, row, conflict = transport.calls[0]
        self.assertEqual(method, "upsert")
        self.assertEqual(table, "letter_processing")
        self.assertEqual(conflict, "letter_id")
        self.assertEqual(row["letter_id"], LETTER_ID)

    def test_context_save_updates_existing_letter_row(self) -> None:
        from unittest.mock import patch

        transport = FakeTransport()
        repository = SupabaseLetterRepository(transport)

        with patch(
            "letter_registry.supabase_repository.build_supabase_context_processing_patch",
            return_value={"letter_id": LETTER_ID, "owner_id": OWNER_ID},
        ), patch(
            "letter_registry.supabase_repository.build_supabase_letter_context_patch",
            return_value={"id": LETTER_ID, "owner_id": OWNER_ID, "title": "Synthetic"},
        ):
            repository.save_context_result(
                record(),
                owner_id=OWNER_ID,
                result=object(),
            )

        self.assertEqual(transport.calls[0][0], "upsert")
        self.assertEqual(transport.calls[0][1], "letter_processing")
        self.assertEqual(transport.calls[1][0], "update")
        self.assertEqual(transport.calls[1][1], "letters")
        self.assertIn(LETTER_ID, transport.calls[1][3])

    def test_adapter_contains_no_runtime_credentials(self) -> None:
        transport = FakeTransport()
        repository = SupabaseLetterRepository(transport)

        self.assertFalse(hasattr(repository, "url"))
        self.assertFalse(hasattr(repository, "api_key"))
        self.assertFalse(hasattr(repository, "access_token"))


if __name__ == "__main__":
    unittest.main()
