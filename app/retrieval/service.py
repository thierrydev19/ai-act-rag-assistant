"""Service de retrieval.

Lot 1: contrat uniquement.
"""

from dataclasses import dataclass

from app.document.models import DocumentChunk, UserQuestion


@dataclass(frozen=True)
class RetrievalResult:
    """Résultat de retrieval incluant les chunks contextuels."""

    chunks: list[DocumentChunk]


class RetrievalService:
    """Expose le contrat de récupération documentaire."""

    def retrieve(self, question: UserQuestion) -> RetrievalResult:
        """Récupère les extraits pertinents pour une question."""
        raise NotImplementedError("Retrieval non implémenté dans le lot 1.")

