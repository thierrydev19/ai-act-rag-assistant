"""Tests du service d'embeddings lot 5."""

from __future__ import annotations

import unittest

from app.embeddings.service import EmbeddingService


class TestEmbeddingService(unittest.TestCase):
    def test_embeddings_are_generated_for_each_text(self) -> None:
        svc = EmbeddingService(dimension=64)
        texts = ["Article 1 obligations", "Article 2 definitions", ""]
        vectors = svc.embed_texts(texts)

        self.assertEqual(len(vectors), 3)
        self.assertTrue(all(len(v) == 64 for v in vectors))
        self.assertTrue(any(abs(x) > 0 for x in vectors[0]))
        self.assertTrue(all(x == 0.0 for x in vectors[2]))

    def test_embeddings_are_deterministic(self) -> None:
        svc = EmbeddingService(dimension=32)
        text = "Conformite IA Act"
        v1 = svc.embed_texts([text])[0]
        v2 = svc.embed_texts([text])[0]
        self.assertEqual(v1, v2)


if __name__ == "__main__":
    unittest.main()

