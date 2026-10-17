from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.ingest_whatsapp_attachment import _max_upload_bytes, _limit


class WhatsAppIntakeLimitTests(unittest.TestCase):
    def test_default_whatsapp_file_size_limit_is_2_gib(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(_max_upload_bytes(), 2 * 1024 * 1024 * 1024)

    def test_whatsapp_size_limit_accepts_2_gib(self):
        with patch.dict("os.environ", {"DLR_WHATSAPP_MAX_UPLOAD_BYTES": str(2 * 1024 * 1024 * 1024)}):
            self.assertEqual(_max_upload_bytes(), 2 * 1024 * 1024 * 1024)

    def test_whatsapp_size_limit_rejects_values_above_2_gib(self):
        with patch.dict("os.environ", {"DLR_WHATSAPP_MAX_UPLOAD_BYTES": str(2 * 1024 * 1024 * 1024 + 1)}):
            with self.assertRaisesRegex(RuntimeError, "2 GiB"):
                _max_upload_bytes()

    def test_whatsapp_size_limit_rejects_non_integer(self):
        with patch.dict("os.environ", {"DLR_WHATSAPP_MAX_UPLOAD_BYTES": "large"}):
            with self.assertRaisesRegex(RuntimeError, "integer"):
                _max_upload_bytes()

    def test_intake_count_limit_accepts_more_than_50000(self):
        with patch.dict("os.environ", {"DLR_WHATSAPP_REAL_INTAKE_LIMIT": "100000"}):
            self.assertEqual(_limit(), 100000)

    def test_intake_count_limit_rejects_values_at_or_below_50000(self):
        for value in ("1", "50000"):
            with patch.dict("os.environ", {"DLR_WHATSAPP_REAL_INTAKE_LIMIT": value}):
                with self.assertRaisesRegex(RuntimeError, "50001 and 1000000"):
                    _limit()

    def test_intake_count_limit_rejects_values_above_one_million(self):
        with patch.dict("os.environ", {"DLR_WHATSAPP_REAL_INTAKE_LIMIT": "1000001"}):
            with self.assertRaisesRegex(RuntimeError, "50001 and 1000000"):
                _limit()

    def test_intake_count_limit_rejects_non_integer(self):
        with patch.dict("os.environ", {"DLR_WHATSAPP_REAL_INTAKE_LIMIT": "many"}):
            with self.assertRaisesRegex(RuntimeError, "integer"):
                _limit()


if __name__ == "__main__":
    unittest.main()
