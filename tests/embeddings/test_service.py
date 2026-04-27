"""Tests du service d'embeddings (V3-2 : Sentence Transformers + legacy hashing).

Deux stratégies à valider :
- ``sentence_transformers_v1`` : nouveau défaut, dimension fixe 384.
- ``hashing_v2`` : legacy conservé pour rollback, dimension paramétrable.

Les tests sur la stratégie ST sont volontairement minimaux pour rester rapides
(le modèle pèse ~120 Mo et le télécharge si nécessaire au premier appel).
"""

from __future__ import annotations

import math
import unittest

from app.embeddings.service import EmbeddingService


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class TestEmbeddingServiceHashingLegacy(unittest.TestCase):
    """Garantit que la stratégie legacy ``hashing_v2`` reste fonctionnelle."""

    def test_embeddings_are_generated_for_each_text(self) -> None:
        svc = EmbeddingService(dimension=96, strategy="hashing_v2")
        texts = ["Article 1 obligations", "Article 2 definitions", ""]
        vectors = svc.embed_texts(texts)

        self.assertEqual(len(vectors), 3)
        self.assertTrue(all(len(v) == 96 for v in vectors))
        self.assertTrue(any(abs(x) > 0 for x in vectors[0]))
        self.assertTrue(all(x == 0.0 for x in vectors[2]))

    def test_embeddings_are_deterministic(self) -> None:
        svc = EmbeddingService(dimension=64, strategy="hashing_v2")
        text = "Conformite IA Act"
        v1 = svc.embed_texts([text])[0]
        v2 = svc.embed_texts([text])[0]
        self.assertEqual(v1, v2)

    def test_embedding_strategy_and_dimension_are_exposed(self) -> None:
        svc = EmbeddingService(dimension=128, strategy="hashing_v2")
        self.assertEqual(svc.dimension, 128)
        self.assertEqual(svc.strategy, "hashing_v2")

    def test_related_texts_are_closer_than_unrelated(self) -> None:
        svc = EmbeddingService(dimension=192, strategy="hashing_v2")
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


class TestEmbeddingServiceSentenceTransformers(unittest.TestCase):
    """Valide la stratégie par défaut : ``sentence_transformers_v1``.

    Ces tests chargent le modèle multilingue (~120 Mo) lors de la première
    exécution. Les exécutions suivantes utilisent le cache global du modèle.
    """

    def test_default_strategy_is_sentence_transformers(self) -> None:
        svc = EmbeddingService()
        self.assertEqual(svc.strategy, "sentence_transformers_v1")
        self.assertEqual(svc.dimension, 384)

    def test_explicit_strategy_sentence_transformers(self) -> None:
        svc = EmbeddingService(strategy="sentence_transformers_v1")
        self.assertEqual(svc.strategy, "sentence_transformers_v1")

    def test_invalid_strategy_raises(self) -> None:
        with self.assertRaises(ValueError):
            EmbeddingService(strategy="random_unknown_strategy")

    def test_st_embeddings_have_correct_shape(self) -> None:
        svc = EmbeddingService(strategy="sentence_transformers_v1")
        texts = ["Article 1 obligations", "Article 2 definitions", ""]
        vectors = svc.embed_texts(texts)

        self.assertEqual(len(vectors), 3)
        self.assertTrue(all(len(v) == 384 for v in vectors))
        # Texte non vide : vecteur non nul.
        self.assertTrue(any(abs(x) > 1e-6 for x in vectors[0]))
        # Texte vide : vecteur zéro (compat. invariant V1).
        self.assertTrue(all(x == 0.0 for x in vectors[2]))

    def test_st_embeddings_are_l2_normalized(self) -> None:
        """Les vecteurs ST doivent avoir une norme L2 ≈ 1 (cosine direct)."""
        svc = EmbeddingService(strategy="sentence_transformers_v1")
        v = svc.embed_texts(["Quelles sont les obligations de transparence ?"])[0]
        norm = math.sqrt(sum(x * x for x in v))
        self.assertAlmostEqual(norm, 1.0, places=4)

    def test_st_embeddings_are_deterministic(self) -> None:
        svc = EmbeddingService(strategy="sentence_transformers_v1")
        v1 = svc.embed_texts(["Définition d'un système d'IA"])[0]
        v2 = svc.embed_texts(["Définition d'un système d'IA"])[0]
        # Tolérance numérique : ST peut avoir d'infimes flottements selon
        # l'ordre des opérations, mais la cosine doit être très élevée.
        sim = _cosine_similarity(v1, v2)
        self.assertGreater(sim, 0.9999)

    def test_st_semantic_understanding_beats_lexical(self) -> None:
        """Le test discriminant V3-2 : les ST doivent comprendre la sémantique
        au-delà du lexical, là où hashing_v2 échouait.

        Cas concret de l'audit V1 : "définit-il" doit s'approcher de
        "définition", même si les mots ne se recoupent pas littéralement.
        """
        svc = EmbeddingService(strategy="sentence_transformers_v1")
        question = svc.embed_texts(
            ["Comment l'AI Act définit-il un système d'intelligence artificielle ?"]
        )[0]
        answer = svc.embed_texts(
            ["Aux fins du présent règlement, on entend par 'système d'IA' un système..."]
        )[0]
        unrelated = svc.embed_texts(
            ["Les recettes de cuisine méditerranéenne avec poisson grillé."]
        )[0]
        sim_relevant = _cosine_similarity(question, answer)
        sim_unrelated = _cosine_similarity(question, unrelated)
        # On exige une marge significative : la pertinence sémantique doit être
        # au moins 0.15 supérieure à la non-pertinence (en pratique on observe
        # ~0.55 vs ~0.05, marge bien plus large).
        self.assertGreater(sim_relevant - sim_unrelated, 0.15)


if __name__ == "__main__":
    unittest.main()
