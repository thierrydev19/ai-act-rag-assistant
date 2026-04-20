"""Service de retrieval semantique (lot 6)."""

from dataclasses import dataclass

from app.embeddings.service import EmbeddingService
from app.embeddings.store import VectorStore
from app.document.models import DocumentChunk, UserQuestion
from app.logging.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class RetrievalResult:
    """Resultat de retrieval avec signal de suffisance documentaire."""

    chunks: list[DocumentChunk]
    is_sufficient: bool
    status: str
    message: str


class RetrievalService:
    """Recherche semantique de chunks pour une question utilisateur."""

    def __init__(
        self,
        *,
        vector_store: VectorStore | None = None,
        embedding_service: EmbeddingService | None = None,
        top_k: int = 5,
        max_acceptable_distance: float = 1.25,
    ) -> None:
        if top_k <= 0:
            raise ValueError("top_k doit etre strictement positif.")
        self._vector_store = vector_store or VectorStore()
        self._embedding_service = embedding_service or EmbeddingService()
        self._top_k = top_k
        self._max_acceptable_distance = max_acceptable_distance

    def retrieve(self, question: UserQuestion) -> RetrievalResult:
        """Recupere les extraits pertinents pour une question."""
        question_text = (question.text or "").strip()
        if not question_text:
            return RetrievalResult(
                chunks=[],
                is_sufficient=False,
                status="insufficient",
                message="Question vide: retrieval impossible.",
            )

        query_embedding = self._embedding_service.embed_texts([question_text])[0]
        hits = self._vector_store.search(query_embedding=query_embedding, top_k=self._top_k)

        if not hits:
            return RetrievalResult(
                chunks=[],
                is_sufficient=False,
                status="insufficient",
                message="Aucun extrait pertinent trouve dans le store.",
            )

        good_hits = [
            hit for hit in hits if hit["distance"] <= self._max_acceptable_distance
        ]
        if not good_hits:
            logger.warning(
                "Retrieval bruite | question=%s | min_distance=%.4f",
                question_text[:80],
                min(hit["distance"] for hit in hits),
            )
            return RetrievalResult(
                chunks=[hit["chunk"] for hit in hits],
                is_sufficient=False,
                status="insufficient",
                message="Extraits trouves mais pertinence insuffisante (distance trop elevee).",
            )

        chunks = [hit["chunk"] for hit in good_hits]
        logger.info(
            "Retrieval | question=%s | chunks=%s",
            question_text[:80],
            len(chunks),
        )
        return RetrievalResult(
            chunks=chunks,
            is_sufficient=True,
            status="sufficient",
            message="Extraits pertinents recuperes.",
        )

