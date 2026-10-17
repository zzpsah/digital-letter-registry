from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.ingest_whatsapp_attachment import _max_upload_bytes, _limit


class WhatsAppIntakeLimitTests(unittest.TestCase):
    def test_default_whatsapp_file_size_limit_remains_20_mib(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(_max_upload_bytes(), 20 * 1024 * 1024)

    def test_whatsapp_size_limit_can_be_bounded_at_100_mib(self):
        with patch.dict("os.environ", {"DLR_WHATSAPP_MAX_UPLOAD_BYTES": str(100 * 1024 * 1024)}):
            self.assertEqual(_max_upload_bytes(), 100 * 1024 * 1024)

    def test_whatsapp_size_limit_rejects_values_above_100_mib(self):
        with patch.dict("os.environ", {"DLR_WHATSAPP_MAX_UPLOAD_BYTES": str(100 * 1024 * 1024 + 1)}):
            with self.assertRaisesRegex(RuntimeError, "100 MiB"):
                _max_upload_bytes()

    def test_whatsapp_size_limit_rejects_non_integer(self):
        with patch.dict("os.environ", {"DLR_WHATSAPP_MAX_UPLOAD_BYTES": "large"}):
            with self.assertRaisesRegex(RuntimeError, "integer"):
                _max_upload_bytes()

    def test_intake_count_limit_remains_bounded_to_500(self):
        with patch.dict("os.environ", {"DLR_WHATSAPP_REAL_INTAKE_LIMIT": "150"}):
            self.assertEqual(_limit(), 150)
        with patch.dict("os.environ", {"DLR_WHATSAPP_REAL_INTAKE_LIMIT": "501"}):
            with self.assertRaisesRegex(RuntimeError, "between 1 and 500"):
                _limit()


if __name__ == "__main__":
    unittest.main()
