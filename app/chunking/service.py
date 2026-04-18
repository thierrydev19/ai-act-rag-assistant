"""Service de chunking.

Lot 1: interface uniquement, sans logique de découpage.
"""

from app.document.models import DocumentChunk


class ChunkingService:
    """Définit le contrat de découpage documentaire."""

    def split(self, raw_chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        """Découpe les contenus selon des règles juridiques.

        Le comportement réel est hors périmètre du lot 1.
        """
        raise NotImplementedError("Chunking non implémenté dans le lot 1.")

