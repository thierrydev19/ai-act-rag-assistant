"""Interface vitrine scenarisee (lot 9)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.chunking.service import ChunkingService
from app.document.models import DocumentChunk, UserQuestion
from app.document.structuring import structure_ingested_pdf
from app.embeddings.store import VectorStore
from app.generation.service import GenerationService
from app.ingestion.service import IngestionService, mvp_ai_act_french_pdf_path
from app.retrieval.service import RetrievalResult, RetrievalService


@dataclass(frozen=True)
class DemoCase:
    """Cas de demonstration maitrise pour la vitrine MVP."""

    case_id: str
    title: str
    question: str
    expected_refusal: bool


@dataclass(frozen=True)
class UiTurnView:
    """Vue de sortie pour afficher un tour question/reponse/citations."""

    question: str
    answer_text: str
    citations: list[str]
    refusal: bool
    intent: str
    retrieval_status: str
    retrieval_message: str


class ShowcaseUI:
    """Facade UI simple pour executer et afficher un parcours de demonstration."""

    def __init__(
        self,
        *,
        retrieval_service: object,
        generation_service: GenerationService,
        demo_cases: list[DemoCase],
    ) -> None:
        self._retrieval = retrieval_service
        self._generation = generation_service
        self._demo_cases = demo_cases

    @property
    def demo_cases(self) -> list[DemoCase]:
        return list(self._demo_cases)

    def ask(self, question: str) -> UiTurnView:
        """Execute un tour complet et retourne une vue directement affichable."""
        user_question = UserQuestion(text=question)
        retrieval_result = self._retrieval.retrieve(user_question)
        answer = self._generation.generate(user_question, retrieval_result)
        return UiTurnView(
            question=question,
            answer_text=answer.answer_text,
            citations=answer.citations,
            refusal=answer.refusal,
            intent=answer.intent,
            retrieval_status=retrieval_result.status,
            retrieval_message=retrieval_result.message,
        )

    def render_turn(self, view: UiTurnView) -> str:
        """Produit un rendu texte lisible pour dirigeants PME et consultants."""
        citations_block = (
            "\n".join(f"- {citation}" for citation in view.citations)
            if view.citations
            else "- Aucune citation exploitable."
        )
        return (
            f"Question: {view.question}\n"
            f"Retrieval: {view.retrieval_status} ({view.retrieval_message})\n\n"
            f"{view.answer_text}\n\n"
            "Citations visibles:\n"
            f"{citations_block}"
        )


class _NullRetrievalService:
    """Retrieval neutre pour initialisation UI sans ecriture disque."""

    def retrieve(self, question: UserQuestion) -> RetrievalResult:
        _ = question
        return RetrievalResult(
            chunks=[],
            is_sufficient=False,
            status="insufficient",
            message="UI initialisee sans corpus indexe.",
        )


def default_demo_cases() -> list[DemoCase]:
    """Retourne les cas de demonstration imposes pour le lot 9."""
    return [
        DemoCase(
            case_id="transparence",
            title="Obligations de transparence",
            question="Quelles obligations de transparence pour les systemes IA ?",
            expected_refusal=False,
        ),
        DemoCase(
            case_id="sanctions",
            title="Sanctions en cas de violation",
            question="Quelles sanctions sont prevues en cas de violation ?",
            expected_refusal=False,
        ),
        DemoCase(
            case_id="definition",
            title="Definition d'un systeme IA",
            question="Comment le reglement definit un systeme IA ?",
            expected_refusal=False,
        ),
        DemoCase(
            case_id="hors_perimetre",
            title="Question hors perimetre",
            question="Quel est le regime fiscal IA mondial detaille par pays ?",
            expected_refusal=True,
        ),
    ]


def build_ui() -> ShowcaseUI:
    """Construit la facade UI sans charger le corpus (initialisation legere)."""
    retrieval = _NullRetrievalService()
    generation = GenerationService()
    return ShowcaseUI(
        retrieval_service=retrieval,
        generation_service=generation,
        demo_cases=default_demo_cases(),
    )


def create_showcase_ui(
    *,
    source_path: str | Path | None = None,
    persist_directory: str | Path = ".chroma_ui",
    collection_name: str = "ai_act_mvp_ui",
    retrieval_top_k: int = 3,
    retrieval_max_distance: float = 1.35,
    demo_cases: list[DemoCase] | None = None,
) -> ShowcaseUI:
    """Construit une UI prete a la demo avec indexation du corpus officiel."""
    pdf_path = Path(source_path) if source_path is not None else mvp_ai_act_french_pdf_path()
    ingested = IngestionService().ingest_pdf(pdf_path)
    structured = structure_ingested_pdf(ingested)
    chunks = ChunkingService().split(structured)
    return create_showcase_ui_from_chunks(
        chunks=chunks,
        persist_directory=persist_directory,
        collection_name=collection_name,
        retrieval_top_k=retrieval_top_k,
        retrieval_max_distance=retrieval_max_distance,
        demo_cases=demo_cases,
    )


def create_showcase_ui_from_chunks(
    *,
    chunks: list[DocumentChunk],
    persist_directory: str | Path = ".chroma_ui",
    collection_name: str = "ai_act_mvp_ui",
    retrieval_top_k: int = 3,
    retrieval_max_distance: float = 1.35,
    demo_cases: list[DemoCase] | None = None,
) -> ShowcaseUI:
    """Construit une UI prete a la demo a partir de chunks deja produits."""
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
    return ShowcaseUI(
        retrieval_service=retrieval,
        generation_service=generation,
        demo_cases=demo_cases or default_demo_cases(),
    )

