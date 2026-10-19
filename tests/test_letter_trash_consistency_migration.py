from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase" / "migrations" / "20261019100000_enforce_letter_trash_consistency.sql"


class LetterTrashConsistencyMigrationTests(unittest.TestCase):
    def test_trash_flag_and_timestamp_are_reconciled(self):
        sql = MIGRATION.read_text(encoding="utf-8").lower()
        self.assertIn("where coalesce(is_trashed, false) = true", sql)
        self.assertIn("where coalesce(is_trashed, false) = false", sql)
        self.assertIn("create or replace function public.sync_letter_trash_state()", sql)
        self.assertIn("create trigger letters_sync_trash_state", sql)

    def test_both_flag_and_timestamp_only_updates_are_handled(self):
        sql = MIGRATION.read_text(encoding="utf-8").lower()
        self.assertIn("new.is_trashed is distinct from old.is_trashed", sql)
        self.assertIn("new.trashed_at is distinct from old.trashed_at", sql)
        self.assertIn("new.trashed_at := coalesce(new.trashed_at, old.trashed_at, now())", sql)
        self.assertIn("new.trashed_at := null", sql)

    def test_database_invariant_is_enforced(self):
        sql = MIGRATION.read_text(encoding="utf-8").lower()
        self.assertIn("letters_trash_state_consistent", sql)
        self.assertIn("check (coalesce(is_trashed, false) = (trashed_at is not null))", sql)
        self.assertIn("validate constraint letters_trash_state_consistent", sql)


if __name__ == "__main__":
    unittest.main()
