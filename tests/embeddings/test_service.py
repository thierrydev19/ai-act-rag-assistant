"""Tests du service d'embeddings lot 5."""

from __future__ import annotations

import math
import unittest

from app.embeddings.service import EmbeddingService


class TestEmbeddingService(unittest.TestCase):
    def test_embeddings_are_generated_for_each_text(self) -> None:
        svc = EmbeddingService(dimension=96)
        texts = ["Article 1 obligations", "Article 2 definitions", ""]
        vectors = svc.embed_texts(texts)

        self.assertEqual(len(vectors), 3)
        self.assertTrue(all(len(v) == 96 for v in vectors))
        self.assertTrue(any(abs(x) > 0 for x in vectors[0]))
        self.assertTrue(all(x == 0.0 for x in vectors[2]))

    def test_embeddings_are_deterministic(self) -> None:
        svc = EmbeddingService(dimension=64)
        text = "Conformite IA Act"
        v1 = svc.embed_texts([text])[0]
        v2 = svc.embed_texts([text])[0]
        self.assertEqual(v1, v2)

    def test_embedding_strategy_and_dimension_are_exposed(self) -> None:
        svc = EmbeddingService(dimension=128, strategy="hashing_v2")
        self.assertEqual(svc.dimension, 128)
        self.assertEqual(svc.strategy, "hashing_v2")

    def test_related_texts_are_closer_than_unrelated(self) -> None:
        svc = EmbeddingService(dimension=192)
        q = svc.embed_texts(["obligations de transparence pour systemes IA"])[0]
        related = svc.embed_texts(
            ["les obligations de transparence imposent des informations claires"]
        )[0]
        unrelated = svc.embed_texts(
            ["recettes de cuisine mediterraneenne et astuces de cuisson"]
        )[0]
        sim_related = _cosine_similarity(q, related)
        sim_unrelated = _cosine_similarity(q, unrelated)
        self.assertGreater(sim_related, sim_unrelated)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


if __name__ == "__main__":
    unittest.main()

