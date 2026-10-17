from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase" / "migrations" / "20261018193000_bound_fts_text_size.sql"

class LargeExtractedTextMigrationTests(unittest.TestCase):
    def test_full_extracted_text_is_not_truncated_or_rewritten(self):
        sql = MIGRATION.read_text(encoding="utf-8")
        self.assertNotIn("UPDATE public.letter_processing", sql.upper())
        self.assertIn("left(coalesce(extracted_text, ''), 50000)", sql)
        self.assertIn("left(p.extracted_text, 50000) as extracted_text", sql)
        self.assertIn("left(p.extracted_text, 50000)", sql)

    def test_search_rpc_uses_bounded_haystack(self):
        sql = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("to_tsvector('simple',b.haystack)", sql)
        self.assertIn("left(p.extracted_text, 50000)", sql)

if __name__ == "__main__":
    unittest.main()
