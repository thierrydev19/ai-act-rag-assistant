"""Préparation des embeddings et accès au stockage vectoriel."""

from app.embeddings.service import EmbeddingService
from app.embeddings.store import VectorStore

__all__ = ["EmbeddingService", "VectorStore"]

