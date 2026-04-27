"""Service de retrieval semantique (lot 6, recalibre V3-3a pour sentence-transformers).

Histoire des calibrations :
- V1 (hashing_v2 ; remediation R2) : seuils calibres sur l'echelle des distances
  produites par hashing local (typiquement 0.0 a 1.8 sur ce corpus).
  max_acceptable_distance=1.35, relaxed_max_distance=1.7, min_lexical_overlap=0.08,
  min_combined_score=0.14.

- V3-3a (sentence-transformers/MiniLM L12 v2 multilingue, normalise L2) :
  les distances cosine restent dans [0.3, 1.2] sur le corpus AI Act 144 pages.
  Recalibration basee sur 15 questions de la grille canonique :
  - 8 positives : distances 0.39 a 0.96, combined 0.39 a 0.74
  - 3 limites : distances 0.61 a 0.96, combined 0.43 a 0.48
  - 4 refus attendus : distances 0.68 a 1.18, combined 0.24 a 0.50
  La distance seule ne separe pas positifs et refus (chevauchement). Le
  combined_score le fait mieux : retenir min_combined_score >= 0.42 rejette
  3 refus sur 4 au retrieval (le 4e est rattrape par le filtrage hors-perimetre
  en aval).

Variables d'environnement (override pour experimentation sans recompiler) :
- AI_ACT_RETRIEVAL_MAX_DISTANCE
- AI_ACT_RETRIEVAL_RELAXED_DISTANCE
- AI_ACT_RETRIEVAL_MIN_LEXICAL
- AI_ACT_RETRIEVAL_MIN_COMBINED
"""

from dataclasses import dataclass
import os
import re

from app.embeddings.service import EmbeddingService
from app.embeddings.store import VectorStore
from app.document.models import DocumentChunk, UserQuestion
from app.logging.logger import get_logger

logger = get_logger(__name__)
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_STOPWORDS = {
    "de", "du", "des", "la", "le", "les", "un", "une", "et", "ou",
    "en", "dans", "sur", "pour", "par", "que", "quelles", "quels",
    "comment", "est", "sont", "aux", "au",
}


def _env_float(name: str, default: float) -> float:
    """Lit un seuil depuis une variable d'env, avec fallback silencieux."""
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        logger.warning("Variable %s invalide (%r), valeur par defaut %s utilisee.", name, raw, default)
        return default


# Defauts V3-3a : calibres pour sentence-transformers normalise L2.
DEFAULT_MAX_ACCEPTABLE_DISTANCE = _env_float("AI_ACT_RETRIEVAL_MAX_DISTANCE", 1.30)
DEFAULT_RELAXED_MAX_DISTANCE = _env_float("AI_ACT_RETRIEVAL_RELAXED_DISTANCE", 1.50)
DEFAULT_MIN_LEXICAL_OVERLAP = _env_float("AI_ACT_RETRIEVAL_MIN_LEXICAL", 0.08)
DEFAULT_MIN_COMBINED_SCORE = _env_float("AI_ACT_RETRIEVAL_MIN_COMBINED", 0.385)


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
        max_acceptable_distance: float = DEFAULT_MAX_ACCEPTABLE_DISTANCE,
        relaxed_max_distance: float = DEFAULT_RELAXED_MAX_DISTANCE,
        min_lexical_overlap: float = DEFAULT_MIN_LEXICAL_OVERLAP,
        min_combined_score: float = DEFAULT_MIN_COMBINED_SCORE,
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
