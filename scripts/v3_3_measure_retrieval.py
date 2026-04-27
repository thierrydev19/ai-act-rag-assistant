"""Script de mesure pour le Lot V3-3 : observation des distances et scores de retrieval
sur la grille canonique de 15 questions, avec les nouveaux embeddings sentence-transformers.

Usage:
    python scripts/v3_3_measure_retrieval.py

Ce script ne modifie aucun code applicatif. Il :
1. Construit le pipeline complet (ingestion, chunking, indexation).
2. Pour chaque question de la grille qualite, calcule les metriques brutes
   (min_distance, best_combined, lexical_overlap, semantic_score) ET le verdict
   du retrieval actuel (avec les seuils calibres pour hashing_v2).
3. Compare le statut observe au statut attendu pour chaque question.
4. Sort un tableau lisible et un rapport markdown dans
   docs/cto/lot_v3_3_measure_report.md.

Apres avoir lu cette mesure, on pourra recalibrer les seuils dans
app/retrieval/service.py (max_acceptable_distance, relaxed_max_distance,
min_lexical_overlap, min_combined_score) sur des donnees reelles plutot que
de deviner.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Permet de lancer le script depuis la racine du repo.
_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from app.chunking.service import ChunkingService
from app.document.models import UserQuestion
from app.document.structuring import structure_ingested_pdf
from app.embeddings.service import EmbeddingService
from app.embeddings.store import VectorStore
from app.ingestion.service import IngestionService, mvp_ai_act_french_pdf_path
from app.retrieval.service import RetrievalService
from app.ui.app import create_showcase_ui
from app.ui.quality_gate import default_quality_questions

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_STOPWORDS = {
    "de", "du", "des", "la", "le", "les", "un", "une", "et", "ou",
    "en", "dans", "sur", "pour", "par", "que", "quelles", "quels",
    "comment", "est", "sont", "aux", "au",
}


@dataclass
class MeasureRow:
    question: str
    expected_status: str
    category: str
    # Mesures brutes (top hit, sans aucun filtrage)
    min_distance: float
    best_combined: float
    best_lexical: float
    best_semantic: float
    # Verdict de la chaine actuelle (ce que voit l'utilisateur)
    observed_status: str
    is_sufficient: bool
    chunks_count: int
    # Decision finale du quality gate (refusal, etc.) via la UI complete
    ui_refusal: bool
    ui_intent: str


def _extract_terms(text: str) -> set[str]:
    return {
        tok.lower()
        for tok in _TOKEN_RE.findall(text or "")
        if len(tok) >= 4 and tok.lower() not in _STOPWORDS
    }


def _lexical_overlap(question_terms: set[str], chunk_text: str) -> float:
    if not question_terms:
        return 0.0
    chunk_terms = _extract_terms(chunk_text)
    if not chunk_terms:
        return 0.0
    return len(question_terms.intersection(chunk_terms)) / len(question_terms)


def _semantic_score(distance: float, cap: float = 1.8) -> float:
    clamped = min(max(distance, 0.0), cap)
    return 1.0 - (clamped / cap)


def measure_question(
    question_text: str,
    embedding_service: EmbeddingService,
    vector_store: VectorStore,
    retrieval_service: RetrievalService,
) -> tuple[float, float, float, float]:
    """Calcule les metriques brutes du top-1 hit (sans filtrage)."""
    query_embedding = embedding_service.embed_texts([question_text])[0]
    hits = vector_store.search(query_embedding=query_embedding, top_k=8)
    if not hits:
        return float("inf"), 0.0, 0.0, 0.0
    question_terms = _extract_terms(question_text)
    best_combined = 0.0
    best_lex = 0.0
    best_sem = 0.0
    min_dist = min(h["distance"] for h in hits)
    for h in hits:
        lex = _lexical_overlap(question_terms, h["chunk"].chunk_text)
        sem = _semantic_score(h["distance"])
        comb = 0.7 * sem + 0.3 * lex
        if comb > best_combined:
            best_combined = comb
            best_lex = lex
            best_sem = sem
    return min_dist, best_combined, best_lex, best_sem


def main() -> int:
    print("Bootstrap pipeline (ingestion + chunking + indexation)...")
    print(f"Strategie embeddings: {EmbeddingService().strategy}")
    print(f"Dimension embeddings: {EmbeddingService().dimension}")
    print()

    # On reutilise la UI complete pour mesurer le verdict utilisateur final.
    ui = create_showcase_ui()

    # On ouvre aussi le retrieval / vector_store / embeddings pour les mesures brutes.
    pdf_path = mvp_ai_act_french_pdf_path()
    if not pdf_path.is_file():
        print(f"ERREUR: PDF officiel introuvable: {pdf_path}")
        return 1

    ingested = IngestionService().ingest_pdf(pdf_path)
    structured = structure_ingested_pdf(ingested)
    chunks = ChunkingService().split(structured)
    embedding_service = EmbeddingService()
    vector_store = VectorStore(embedding_service=embedding_service)
    vector_store.index(chunks)
    retrieval_service = RetrievalService(
        vector_store=vector_store,
        embedding_service=embedding_service,
    )
    print(f"Indexes: {len(chunks)} chunks")
    print()

    # Mesure de chaque question.
    questions = default_quality_questions()
    rows: list[MeasureRow] = []
    for q in questions:
        # Mesures brutes de retrieval.
        min_dist, best_comb, best_lex, best_sem = measure_question(
            q.question, embedding_service, vector_store, retrieval_service
        )
        # Verdict de la chaine retrieval (avec les seuils actuels).
        retrieval_result = retrieval_service.retrieve(UserQuestion(text=q.question))
        # Verdict de l'UI complete (refusal final ou non).
        turn = ui.ask(q.question)
        rows.append(MeasureRow(
            question=q.question,
            expected_status=q.expected_status,
            category=q.category,
            min_distance=min_dist,
            best_combined=best_comb,
            best_lexical=best_lex,
            best_semantic=best_sem,
            observed_status=retrieval_result.status,
            is_sufficient=retrieval_result.is_sufficient,
            chunks_count=len(retrieval_result.chunks),
            ui_refusal=turn.refusal,
            ui_intent=turn.intent,
        ))

    # Affichage console.
    _print_table(rows)

    # Rapport markdown.
    report_path = _REPO_ROOT / "docs" / "cto" / "lot_v3_3_measure_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_format_markdown(rows), encoding="utf-8")
    print(f"\nRapport ecrit dans: {report_path}")
    return 0


def _print_table(rows: list[MeasureRow]) -> None:
    headers = [
        "Cat.", "Question (40)", "Att.", "Obs.", "Suff.",
        "minDist", "bestComb", "bestLex", "bestSem", "Refus", "Intent",
    ]
    print(" | ".join(headers))
    print("-" * 140)
    for r in rows:
        print(" | ".join([
            r.category[:5].ljust(5),
            r.question[:40].ljust(40),
            r.expected_status[:8].ljust(8),
            r.observed_status[:8].ljust(8),
            "Y" if r.is_sufficient else "N",
            f"{r.min_distance:.3f}" if r.min_distance != float("inf") else "  inf",
            f"{r.best_combined:.3f}",
            f"{r.best_lexical:.3f}",
            f"{r.best_semantic:.3f}",
            "Y" if r.ui_refusal else "N",
            r.ui_intent[:14].ljust(14),
        ]))


def _format_markdown(rows: list[MeasureRow]) -> str:
    lines = [
        "# Lot V3-3 — Mesure des distances et scores de retrieval",
        "",
        "Mesures realisees avec :",
        "- Corpus: AI Act FR officiel (UE 2024/1689), 144 pages, 230 chunks",
        f"- Embeddings: {EmbeddingService().strategy} ({EmbeddingService().dimension} dim)",
        "- Seuils retrieval actuels (calibres pour hashing_v2) :",
        "  - max_acceptable_distance = 1.35",
        "  - relaxed_max_distance = 1.7",
        "  - min_lexical_overlap = 0.08",
        "  - min_combined_score = 0.14",
        "",
        "## Synthese",
        "",
    ]
    correct_positive = sum(
        1 for r in rows
        if r.expected_status == "positive" and r.is_sufficient and not r.ui_refusal
    )
    total_positive = sum(1 for r in rows if r.expected_status == "positive")
    correct_refusal = sum(
        1 for r in rows
        if r.expected_status == "refusal" and r.ui_refusal
    )
    total_refusal = sum(1 for r in rows if r.expected_status == "refusal")
    lines.append(f"- Questions positives correctement servies : {correct_positive}/{total_positive}")
    lines.append(f"- Refus correctement detectes : {correct_refusal}/{total_refusal}")
    lines.append("")
    lines.append("## Tableau detaille")
    lines.append("")
    lines.append("| Cat. | Question | Attendu | Observe | Suffisant | min_dist | best_comb | best_lex | best_sem | UI refus | Intent |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        suff = "Y" if r.is_sufficient else "N"
        ref = "Y" if r.ui_refusal else "N"
        min_d = f"{r.min_distance:.3f}" if r.min_distance != float("inf") else "inf"
        lines.append(
            f"| {r.category} | {r.question} | {r.expected_status} | {r.observed_status} | "
            f"{suff} | {min_d} | {r.best_combined:.3f} | "
            f"{r.best_lexical:.3f} | {r.best_semantic:.3f} | {ref} | {r.ui_intent} |"
        )
    lines.append("")
    lines.append("## Lecture")
    lines.append("")
    lines.append("- **min_dist** : distance Chroma du chunk le plus proche (sentence-transformers normalise => 0.0 = identique, 2.0 = oppose).")
    lines.append("- **best_comb** : meilleur score combine (0.7 * semantique + 0.3 * lexical) parmi le top-8.")
    lines.append("- **Suffisant=Y** + **UI refus=N** = cas servi correctement (ce qu'on veut sur les 'positive').")
    lines.append("- **Suffisant=N** + **UI refus=Y** = refus declenche (attendu sur les 'refusal').")
    lines.append("- Les cases qui sortent du pattern sont a etudier pour la recalibration V3-3.")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
