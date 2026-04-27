"""Service d'embeddings textuels pour le MVP (lot V3-2 : embeddings sémantiques).

Stratégies disponibles :

- ``sentence_transformers_v1`` (défaut depuis V3-2) :
  modèle ``sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2``,
  multilingue (50+ langues dont FR), 384 dimensions, ~118 Mo.
  Le modèle est chargé une seule fois au premier appel et réutilisé.
  Les vecteurs sont normalisés L2 pour permettre la cosine similarity directe.

- ``hashing_v2`` (legacy, conservé pour rollback) :
  hashing dense déterministe local, 256 dimensions par défaut. Pas de
  sémantique réelle, conservé uniquement pour fallback en cas de problème
  de déploiement (taille modèle, latence cold-start, etc.).

Note de migration : avec les Sentence Transformers, la ``dimension``
fournie par l'appelant est ignorée — le modèle a une dimension fixe (384).
Le paramètre est conservé pour compatibilité avec les tests legacy mais
n'a plus de sémantique propre.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
import threading
import unicodedata
from typing import Optional

from app.logging.logger import get_logger

logger = get_logger(__name__)

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_STOPWORDS_FR = {
    "de", "du", "des", "la", "le", "les", "un", "une", "et", "ou",
    "en", "dans", "sur", "pour", "par", "au", "aux", "a", "d", "l",
}

# Identifiant du modèle ST. Multilingue, optimisé phrases, 384 dims.
# Choisi pour : (a) couverture FR native, (b) taille raisonnable (~118 Mo),
# (c) bonne performance sur tâches de retrieval / paraphrasing.
_ST_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_ST_DIMENSION = 384

# Stratégies acceptées
_STRATEGY_ST = "sentence_transformers_v1"
_STRATEGY_HASHING = "hashing_v2"
_DEFAULT_STRATEGY = _STRATEGY_ST


def _resolve_default_strategy() -> str:
    """Permet de forcer la stratégie via variable d'env (utile en CI / Railway).

    Valeurs reconnues :
    - ``AI_ACT_EMBEDDING_STRATEGY=hashing_v2`` : retour à l'ancien hashing local
    - ``AI_ACT_EMBEDDING_STRATEGY=sentence_transformers_v1`` : explicite (défaut)
    - non définie : défaut = sentence_transformers_v1
    """
    raw = os.getenv("AI_ACT_EMBEDDING_STRATEGY", "").strip().lower()
    if raw in {_STRATEGY_HASHING, _STRATEGY_ST}:
        return raw
    return _DEFAULT_STRATEGY


# Cache global du modèle Sentence Transformers, partagé entre instances.
# Le chargement est coûteux (~3-5s + ~120 Mo RAM) ; on ne le fait qu'une fois
# par processus. Verrou pour éviter le double-chargement en multi-threads.
_st_model_lock = threading.Lock()
_st_model_cache: Optional[object] = None


def _get_st_model() -> object:
    """Retourne le modèle Sentence Transformers, chargé paresseusement."""
    global _st_model_cache
    if _st_model_cache is not None:
        return _st_model_cache
    with _st_model_lock:
        if _st_model_cache is not None:
            return _st_model_cache
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "sentence-transformers n'est pas installé. "
                "Lancer `pip install sentence-transformers` ou utiliser "
                "AI_ACT_EMBEDDING_STRATEGY=hashing_v2 pour repli."
            ) from exc
        logger.info(
            "Chargement modèle Sentence Transformers | model=%s "
            "(premier appel : ~3-10s, télécharge ~120Mo si non cache)",
            _ST_MODEL_NAME,
        )
        _st_model_cache = SentenceTransformer(_ST_MODEL_NAME)
        logger.info(
            "Modèle Sentence Transformers chargé | dim=%s",
            _ST_DIMENSION,
        )
        return _st_model_cache


class EmbeddingService:
    """Génère des vecteurs déterministes pour chunks et questions.

    Compatible API V1 : ``EmbeddingService(dimension=N, strategy=...)`` où
    ``dimension`` est respecté pour ``hashing_v2`` et ignoré pour
    ``sentence_transformers_v1`` (dimension fixée à 384 par le modèle).
    """

    def __init__(
        self,
        dimension: int = _ST_DIMENSION,
        strategy: Optional[str] = None,
    ) -> None:
        if dimension <= 0:
            raise ValueError("dimension doit être strictement positive.")
        chosen = (strategy or _resolve_default_strategy()).strip()
        if chosen not in {_STRATEGY_ST, _STRATEGY_HASHING}:
            raise ValueError(
                f"Stratégie d'embedding non supportée: {chosen!r}. "
                f"Valeurs : {_STRATEGY_ST!r} ou {_STRATEGY_HASHING!r}."
            )
        self._strategy = chosen
        if chosen == _STRATEGY_ST:
            # Dimension fixée par le modèle ; on ignore le paramètre.
            if dimension != _ST_DIMENSION:
                logger.debug(
                    "Paramètre dimension=%s ignoré pour stratégie %s "
                    "(dimension fixée à %s par le modèle).",
                    dimension, chosen, _ST_DIMENSION,
                )
            self._dimension = _ST_DIMENSION
        else:
            self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def strategy(self) -> str:
        return self._strategy

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Retourne un embedding par texte, dans le même ordre."""
        if self._strategy == _STRATEGY_ST:
            vectors = self._embed_sentence_transformers(texts)
        else:
            vectors = [self._embed_hashing_v2(text) for text in texts]
        if len(vectors) != len(texts):
            raise RuntimeError("Nombre d'embeddings incohérent avec les textes.")
        return vectors

    # --- Stratégie Sentence Transformers (par défaut depuis V3-2) ---

    def _embed_sentence_transformers(self, texts: list[str]) -> list[list[float]]:
        """Encode les textes via le modèle multilingue, normalisés L2.

        Les textes vides sont remplacés par un vecteur zéro (cohérent avec
        l'ancien comportement hashing_v2, et permet d'éviter NaN en cas de
        chunk vide).
        """
        # Préserve l'invariant "texte vide → vecteur zéro" (compat. tests V1).
        non_empty_indices = [i for i, t in enumerate(texts) if (t or "").strip()]
        non_empty_texts = [texts[i] for i in non_empty_indices]

        result: list[list[float]] = [[0.0] * self._dimension for _ in texts]
        if not non_empty_texts:
            return result

        model = _get_st_model()
        # Encodage batch ; normalisation L2 incluse (cosine = produit scalaire).
        encoded = model.encode(
            non_empty_texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        for src_idx, dest_idx in enumerate(non_empty_indices):
            result[dest_idx] = encoded[src_idx].tolist()
        return result

    # --- Stratégie hashing_v2 (legacy, conservée pour rollback) ---

    def _embed_hashing_v2(self, text: str) -> list[float]:
        normalized = self._normalize_text(text or "")
        tokens = _TOKEN_RE.findall(normalized)
        if not tokens:
            return [0.0] * self._dimension

        vec = [0.0] * self._dimension
        weighted_features = self._build_weighted_features(tokens, normalized)
        for feature, weight in weighted_features:
            digest = hashlib.sha256(feature.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], byteorder="big") % self._dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[idx] += sign * weight

        norm = sum(value * value for value in vec) ** 0.5
        if norm == 0:
            return vec
        return [value / norm for value in vec]

    def _normalize_text(self, text: str) -> str:
        ascii_text = (
            unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        )
        return ascii_text.lower()

    def _build_weighted_features(
        self, tokens: list[str], normalized_text: str
    ) -> list[tuple[str, float]]:
        token_counts: dict[str, int] = {}
        for token in tokens:
            lemma = self._light_stem(token)
            token_counts[lemma] = token_counts.get(lemma, 0) + 1

        features: list[tuple[str, float]] = []
        for lemma, count in token_counts.items():
            if lemma in _STOPWORDS_FR:
                continue
            weight = 1.0 + math.log1p(count)
            features.append((f"uni:{lemma}", weight))

        for left, right in zip(tokens, tokens[1:], strict=False):
            l_lemma = self._light_stem(left)
            r_lemma = self._light_stem(right)
            if l_lemma in _STOPWORDS_FR and r_lemma in _STOPWORDS_FR:
                continue
            features.append((f"bi:{l_lemma}_{r_lemma}", 0.65))

        compact = normalized_text.replace(" ", "")
        for i in range(0, max(0, len(compact) - 2), 2):
            tri = compact[i : i + 3]
            if len(tri) == 3:
                features.append((f"char3:{tri}", 0.2))

        return features

    def _light_stem(self, token: str) -> str:
        if len(token) <= 4:
            return token
        for suffix in (
            "ements", "ement", "ations", "ation", "teurs", "teur",
            "euses", "euse", "ments", "ment", "ions", "ion",
            "iques", "ique", "istes", "iste", "eurs", "eaux", "eau",
            "aux", "es", "s",
        ):
            if token.endswith(suffix) and len(token) - len(suffix) >= 3:
                return token[: -len(suffix)]
        return token
