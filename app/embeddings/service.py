"""Service d'embeddings textuels pour le MVP (remediation R1).

Strategie retenue:
- ``hashing_v2`` (defaut): hashing dense avec normalisation linguistique legere,
  unigrams + bigrams + trigrams caracteres, et ponderation simple.
- but: rester local, deterministic, sans rupture d'architecture, avec meilleure
  sensibilite semantique qu'un hashing unigramme minimal.
"""

from __future__ import annotations

import hashlib
import math
import unicodedata
import re

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_STOPWORDS_FR = {
    "de",
    "du",
    "des",
    "la",
    "le",
    "les",
    "un",
    "une",
    "et",
    "ou",
    "en",
    "dans",
    "sur",
    "pour",
    "par",
    "au",
    "aux",
    "a",
    "d",
    "l",
}


class EmbeddingService:
    """Genere des vecteurs deterministes pour chunks et questions."""

    def __init__(self, dimension: int = 256, strategy: str = "hashing_v2") -> None:
        if dimension <= 0:
            raise ValueError("dimension doit être strictement positive.")
        if strategy != "hashing_v2":
            raise ValueError("Strategie d'embedding non supportee.")
        self._dimension = dimension
        self._strategy = strategy

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def strategy(self) -> str:
        return self._strategy

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Retourne un embedding par texte, dans le même ordre."""
        vectors = [self._embed_hashing_v2(text) for text in texts]
        if len(vectors) != len(texts):
            raise RuntimeError("Nombre d'embeddings incohérent avec les textes.")
        return vectors

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
            # TF stabilisee pour eviter qu'un token frequent domine.
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
        for suffix in ("ements", "ement", "ations", "ation", "teurs", "teur", "euses", "euse", "ments", "ment", "ions", "ion", "iques", "ique", "istes", "iste", "eurs", "eaux", "eau", "aux", "es", "s"):
            if token.endswith(suffix) and len(token) - len(suffix) >= 3:
                return token[: -len(suffix)]
        return token

