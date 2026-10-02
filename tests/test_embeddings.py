import json
import unittest

from letter_registry.embeddings import chunk_text
from letter_registry.gemini_embeddings import GeminiEmbeddingProvider


class EmbeddingTests(unittest.TestCase):
    def test_chunking_is_deterministic_with_overlap(self) -> None:
        text = " ".join(f"word{i}" for i in range(500))
        chunks = chunk_text(
            text,
            max_characters=300,
            overlap_characters=40,
        )

        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks[0].index, 0)
        self.assertEqual(chunks[1].index, 1)
        self.assertTrue(chunks[0].content)
        self.assertTrue(chunks[1].content)

    def test_gemini_embedding_maps_exact_dimensions(self) -> None:
        seen = {}

        def executor(req):
            seen["url"] = req.full_url
            seen["payload"] = json.loads(req.data.decode("utf-8"))
            return 200, json.dumps(
                {"embedding": {"values": [0.25] * 8}}
            )

        provider = GeminiEmbeddingProvider(
            api_key="synthetic-key",
            model="gemini-embedding-2",
            dimensions=8,
            http_executor=executor,
        )

        result = provider.embed_query("inter exam last date")

        self.assertEqual(len(result.values), 8)
        self.assertIn("gemini-embedding-2:embedContent", seen["url"])
        self.assertEqual(
            seen["payload"]["output_dimensionality"],
            8,
        )
        self.assertNotIn("embedContentConfig", seen["payload"])
        self.assertIn("retrieving relevant official", seen["payload"]["content"]["parts"][0]["text"])

    def test_blank_embedding_input_is_rejected(self) -> None:
        provider = GeminiEmbeddingProvider(
            api_key="synthetic",
            dimensions=8,
            http_executor=lambda req: (200, "{}"),
        )
        with self.assertRaises(ValueError):
            provider.embed_document("   ")


if __name__ == "__main__":
    unittest.main()
