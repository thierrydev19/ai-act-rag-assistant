"""Service de retrieval semantique (lot 6, calibre R2)."""

from dataclasses import dataclass
import re

from app.embeddings.service import EmbeddingService
from app.embeddings.store import VectorStore
from app.document.models import DocumentChunk, UserQuestion
from app.logging.logger import get_logger

logger = get_logger(__name__)
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_STOPWORDS = {
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
    "que",
    "quelles",
    "quels",
    "comment",
    "est",
    "sont",
    "aux",
    "au",
}


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
        max_acceptable_distance: float = 1.35,
        relaxed_max_distance: float = 1.7,
        min_lexical_overlap: float = 0.08,
        min_combined_score: float = 0.14,
        candidate_pool_factor: int = 4,
    ) -> None:
        if top_k <= 0:
            raise ValueError("top_k doit etre strictement positif.")
        if candidate_pool_factor <= 0:
            raise ValueError("candidate_pool_factor doit etre strictement positif.")
        self._vector_store = vector_store or VectorStore()
        self._embedding_service = embedding_service or EmbeddingService()
        self._top_k = top_k
        self._max_acceptable_distance = max_acceptable_distance
        self._relaxed_max_distance = relaxed_max_distance
        self._min_lexical_overlap = min_lexical_overlap
        self._min_combined_score = min_combined_score
        self._candidate_pool_factor = candidate_pool_factor

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
        pool_size = max(self._top_k, self._top_k * self._candidate_pool_factor)
        hits = self._vector_store.search(query_embedding=query_embedding, top_k=pool_size)

        if not hits:
            return RetrievalResult(
                chunks=[],
                is_sufficient=False,
                status="insufficient",
                message="Aucun extrait pertinent trouve dans le store.",
            )

        question_terms = self._extract_terms(question_text)
        scored_hits = []
        for hit in hits:
            chunk_text = hit["chunk"].chunk_text
            lexical_overlap = self._lexical_overlap(question_terms, chunk_text)
            semantic_score = self._semantic_score(hit["distance"])
            combined_score = 0.7 * semantic_score + 0.3 * lexical_overlap
            scored_hits.append(
                {
                    **hit,
                    "lexical_overlap": lexical_overlap,
                    "semantic_score": semantic_score,
                    "combined_score": combined_score,
                }
            )

        scored_hits.sort(key=lambda item: item["combined_score"], reverse=True)
        good_hits = [
            hit
            for hit in scored_hits
            if (
                hit["distance"] <= self._max_acceptable_distance
                or (
                    hit["distance"] <= self._relaxed_max_distance
                    and hit["lexical_overlap"] >= self._min_lexical_overlap
                )
            )
            and hit["combined_score"] >= self._min_combined_score
        ][: self._top_k]

        if not good_hits:
            logger.warning(
                (
                    "Retrieval bruite | question=%s | min_distance=%.4f "
                    "| best_combined=%.4f"
                ),
                question_text[:80],
                min(hit["distance"] for hit in hits),
                max(hit["combined_score"] for hit in scored_hits),
            )
            return RetrievalResult(
                chunks=[hit["chunk"] for hit in scored_hits[: self._top_k]],
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

    def _extract_terms(self, text: str) -> set[str]:
        terms = {
            tok.lower()
            for tok in _TOKEN_RE.findall(text or "")
            if len(tok) >= 4 and tok.lower() not in _STOPWORDS
        }
        return terms

    def _lexical_overlap(self, question_terms: set[str], chunk_text: str) -> float:
        if not question_terms:
            return 0.0
        chunk_terms = self._extract_terms(chunk_text)
        if not chunk_terms:
            return 0.0
        return len(question_terms.intersection(chunk_terms)) / len(question_terms)

    def _semantic_score(self, distance: float) -> float:
        # Distance Chroma plus petite = plus proche. 0 -> 1.0 ; 1.8 -> 0.0
        cap = 1.8
        clamped = min(max(distance, 0.0), cap)
        return 1.0 - (clamped / cap)

