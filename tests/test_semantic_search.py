import unittest

from letter_registry.semantic_search import (
    SupabaseEmbeddingRepository,
    vector_literal,
)


class FakeEmbeddingProvider:
    version = "fake-embedding-v1"
    dimensions = 3

    def embed_document(self, text):
        from letter_registry.embeddings import EmbeddingResult
        return EmbeddingResult((0.1, 0.2, 0.3), self.version)

    def embed_query(self, text):
        from letter_registry.embeddings import EmbeddingResult
        return EmbeddingResult((0.4, 0.5, 0.6), self.version)


class FakeTransport:
    def __init__(self):
        self.upserts = []
        self.rpcs = []

    def upsert(self, table, row, *, on_conflict):
        self.upserts.append((table, row, on_conflict))
        return row

    def rpc(self, function, params):
        self.rpcs.append((function, params))
        return [
            {
                "letter_id": "22222222-2222-4222-8222-222222222222",
                "chunk_index": 0,
                "content": "synthetic",
                "semantic_similarity": 0.87,
            }
        ]


class SemanticSearchTests(unittest.TestCase):
    def test_vector_literal_is_pgvector_compatible(self):
        self.assertEqual(vector_literal((0.1, 0.2, 0.3)), "[0.1,0.2,0.3]")

    def test_document_chunks_are_embedded_and_upserted(self):
        transport = FakeTransport()
        repo = SupabaseEmbeddingRepository(
            transport=transport,
            provider=FakeEmbeddingProvider(),
        )

        count = repo.embed_document_chunks(
            owner_id="11111111-1111-4111-8111-111111111111",
            letter_id="22222222-2222-4222-8222-222222222222",
            extracted_text="synthetic education letter text " * 30,
            max_characters=250,
            overlap_characters=25,
        )

        self.assertGreater(count, 1)
        self.assertEqual(transport.upserts[0][0], "letter_chunks")
        self.assertEqual(
            transport.upserts[0][2],
            "letter_id,chunk_index,embedding_version",
        )

    def test_semantic_search_uses_embedding_version(self):
        transport = FakeTransport()
        repo = SupabaseEmbeddingRepository(
            transport=transport,
            provider=FakeEmbeddingProvider(),
        )

        rows = repo.semantic_search("inter exam last date", limit=10)

        self.assertEqual(rows[0]["semantic_similarity"], 0.87)
        self.assertEqual(
            transport.rpcs[0][1]["query_embedding_version"],
            "fake-embedding-v1",
        )


if __name__ == "__main__":
    unittest.main()
