import os
import unittest
from unittest.mock import patch

from letter_registry.versions import current_processing_versions


class ProcessingVersionRegistryTests(unittest.TestCase):
    def test_defaults_match_current_pipeline(self):
        with patch.dict(os.environ, {}, clear=True):
            versions = current_processing_versions()

        self.assertEqual(
            versions.extraction_pdf_ocr,
            "ocr-pdf-hi-en-v1",
        )
        self.assertEqual(
            versions.filename_rule_version,
            "official-v1",
        )
        self.assertEqual(
            versions.embedding_version,
            "gemini:gemini-embedding-2:768:v1",
        )
        self.assertEqual(
            versions.status_rule_version,
            "relationships-v1",
        )

    def test_reprocessing_targets_use_current_registry(self):
        with patch.dict(
            os.environ,
            {
                "AI_MODEL": "synthetic-context-model",
                "EMBEDDING_MODEL": "synthetic-embed-model",
                "EMBEDDING_DIMENSIONS": "512",
            },
            clear=True,
        ):
            targets = current_processing_versions().reprocessing_targets()

        self.assertEqual(
            targets.context_version,
            "gemini:synthetic-context-model:context-v1",
        )
        self.assertEqual(
            targets.embedding_version,
            "gemini:synthetic-embed-model:512:v1",
        )


if __name__ == "__main__":
    unittest.main()
