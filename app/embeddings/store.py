"""Contrat de stockage vectoriel (lot 1)."""

from app.document.models import DocumentChunk


class VectorStore:
    """Interface minimale de persistance/recherche vectorielle."""

    def index(self, chunks: list[DocumentChunk]) -> None:
        """Indexe les chunks dans un stockage vectoriel."""
        raise NotImplementedError("Indexation non implémentée dans le lot 1.")

