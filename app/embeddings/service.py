"""Service d'embeddings textuels pour le MVP (lot 5)."""

from __future__ import annotations

import hashlib
import re

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


class EmbeddingService:
    """Génère des vecteurs déterministes pour les chunks documentaires."""

    def __init__(self, dimension: int = 128) -> None:
        if dimension <= 0:
            raise ValueError("dimension doit être strictement positive.")
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Retourne un embedding par texte, dans le même ordre."""
        vectors = [self._embed_single(text) for text in texts]
        if len(vectors) != len(texts):
            raise RuntimeError("Nombre d'embeddings incohérent avec les textes.")
        return vectors

    def _embed_single(self, text: str) -> list[float]:
        tokens = _TOKEN_RE.findall((text or "").lower())
        if not tokens:
            return [0.0] * self._dimension

        vec = [0.0] * self._dimension
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:2], byteorder="big") % self._dimension
            sign = 1.0 if digest[2] % 2 == 0 else -1.0
            vec[idx] += sign

        norm = sum(value * value for value in vec) ** 0.5
        if norm == 0:
            return vec
        return [value / norm for value in vec]

