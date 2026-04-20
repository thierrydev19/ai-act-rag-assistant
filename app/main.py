"""Point d'entree applicatif du socle MVP."""

from dataclasses import dataclass
from pathlib import Path

from app.chunking.service import ChunkingService
from app.document.models import DocumentChunk, UserQuestion
from app.document.structuring import structure_ingested_pdf
from app.embeddings.store import VectorStore
from app.generation.service import AnswerPayload, GenerationService
from app.ingestion.service import IngestionService, mvp_ai_act_french_pdf_path
from app.retrieval.service import RetrievalResult, RetrievalService
from app.ui.app import build_ui


@dataclass(frozen=True)
class AppBootstrap:
    """Indique les modules structurants prêts pour les lots suivants."""

    ingestion: str = "ready"
    document: str = "ready"
    chunking: str = "ready"
    embeddings: str = "ready"
    retrieval: str = "ready"
    generation: str = "ready"
    ui: str = "ready"
    logging: str = "ready"


def bootstrap() -> AppBootstrap:
    """Construit un état minimal de démarrage sans pipeline réel."""
    _ = build_ui()
    return AppBootstrap()


@dataclass(frozen=True)
class E2ETurnResult:
    """Resultat d'un tour complet question -> retrieval -> generation."""

    question: UserQuestion
    retrieval: RetrievalResult
    answer: AnswerPayload


def run_e2e_demo(
    questions: list[UserQuestion],
    *,
    source_path: str | Path | None = None,
    chunks: list[DocumentChunk] | None = None,
    persist_directory: str | Path = ".chroma_e2e",
    collection_name: str = "ai_act_mvp_e2e",
    retrieval_top_k: int = 3,
    retrieval_max_distance: float = 1.35,
) -> list[E2ETurnResult]:
    """Execute un scenario e2e minimal, sans UI et sans refonte des modules."""
    if chunks is None:
        pdf_path = Path(source_path) if source_path is not None else mvp_ai_act_french_pdf_path()
        ingested = IngestionService().ingest_pdf(pdf_path)
        structured = structure_ingested_pdf(ingested)
        chunks = ChunkingService().split(structured)

    store = VectorStore(
        persist_directory=persist_directory,
        collection_name=collection_name,
    )
    store.index(chunks)
    retrieval = RetrievalService(
        vector_store=store,
        top_k=retrieval_top_k,
        max_acceptable_distance=retrieval_max_distance,
    )
    generation = GenerationService()

    results: list[E2ETurnResult] = []
    for question in questions:
        retrieval_result = retrieval.retrieve(question)
        answer_payload = generation.generate(question, retrieval_result)
        results.append(
            E2ETurnResult(
                question=question,
                retrieval=retrieval_result,
                answer=answer_payload,
            )
        )
    return results

