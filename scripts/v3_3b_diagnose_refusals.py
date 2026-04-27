"""Diagnostic precis : pourquoi Q5 et Q8 sont refusees alors que le retrieval renvoie des chunks ?

Inspecte la cascade de refus dans generation/service.py :
1. selection.core_chunks vide ?
2. selection.is_coherent = False ?
3. selection.intent_aligned = False ?

Pour chaque question problematique, on affiche :
- l'intent classifie
- les scores chunk par chunk dans evidence_selection
- le diagnostic du refus

Usage:
    python scripts/v3_3b_diagnose_refusals.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from app.document.models import UserQuestion
from app.generation.evidence_selection import EvidenceSelector
from app.generation.service import GenerationService
from app.retrieval.service import RetrievalService
from app.ui.app import create_showcase_ui


# Questions a diagnostiquer (positifs attendus refuses en V3-3a).
QUESTIONS_TO_DIAGNOSE = [
    "Que faut-il verifier avant de mettre un systeme IA sur le marche ?",
    "Quels points de conformite sont attendus pour les fournisseurs ?",
    # Ajout d'un cas qui MARCHE pour comparer.
    "Quelles obligations existent pour les systemes IA a haut risque ?",
]


def main() -> int:
    print("Bootstrap UI complete...")
    ui = create_showcase_ui()
    # On accede aux services internes via la UI.
    retrieval = ui._retrieval  # type: ignore[attr-defined]
    generation = ui._generation  # type: ignore[attr-defined]
    selector = generation._selector  # type: ignore[attr-defined]
    print("UI prete.")
    print()

    for question_text in QUESTIONS_TO_DIAGNOSE:
        print("=" * 100)
        print(f"QUESTION : {question_text}")
        print("=" * 100)

        # Etape 1 : retrieval
        retrieval_result = retrieval.retrieve(UserQuestion(text=question_text))
        print(f"\n[1] RETRIEVAL")
        print(f"    is_sufficient = {retrieval_result.is_sufficient}")
        print(f"    chunks count  = {len(retrieval_result.chunks)}")
        print(f"    status        = {retrieval_result.status}")
        for i, chunk in enumerate(retrieval_result.chunks):
            article = chunk.metadata.article_ref or "(no article)"
            page = chunk.metadata.page_number
            preview = chunk.chunk_text[:120].replace("\n", " ")
            print(f"    chunk {i}: {article} p.{page} | {preview}...")

        if not retrieval_result.is_sufficient:
            print("\n  -> REFUS au retrieval (Suff=N). Pas le bon diagnostic ici.")
            print()
            continue

        # Etape 2 : intent classification (interne au generation)
        try:
            intent = generation._classify_intent(question_text)  # type: ignore[attr-defined]
        except Exception as exc:
            print(f"\n  ERREUR intent classification : {exc}")
            continue
        print(f"\n[2] INTENT CLASSIFICATION")
        print(f"    intent = {intent!r}")

        # Etape 3 : evidence selection
        selection = selector.select(
            question_text=question_text,
            chunks=retrieval_result.chunks,
            intent=intent,
        )
        print(f"\n[3] EVIDENCE SELECTION")
        print(f"    core_chunks count    = {len(selection.core_chunks)}")
        print(f"    secondary count      = {len(selection.secondary_chunks)}")
        print(f"    rejected count       = {len(selection.rejected_chunks)}")
        print(f"    is_coherent          = {selection.is_coherent}")
        print(f"    intent_aligned       = {selection.intent_aligned}")
        print(f"    message              = {selection.message}")

        # Detail des scores (recalcul pour transparence).
        print(f"\n  Detail scoring chunks:")
        question_tokens = selector._question_tokens(question_text)  # type: ignore[attr-defined]
        for i, chunk in enumerate(retrieval_result.chunks):
            score = selector._score_chunk(  # type: ignore[attr-defined]
                question_tokens=question_tokens, chunk=chunk, intent=intent
            )
            article = chunk.metadata.article_ref or "(no article)"
            in_core = chunk in selection.core_chunks
            in_sec = chunk in selection.secondary_chunks
            in_rej = chunk in selection.rejected_chunks
            tag = "CORE" if in_core else ("SEC " if in_sec else ("REJ " if in_rej else "??? "))
            print(f"    {tag} chunk {i}: score={score:.4f} | {article} | min_score={selector._min_score}")

        # Etape 4 : diagnostic de la cascade de refus dans generation_service
        print(f"\n[4] DIAGNOSTIC DE LA CASCADE DE REFUS")
        if not selection.core_chunks:
            print("    >>> REFUS DECLENCHE : selection.core_chunks vide <<<")
            print("        -> Aucun chunk n'a obtenu de score >= min_score (0.06).")
        elif not selection.is_coherent:
            print("    >>> REFUS DECLENCHE : selection.is_coherent = False <<<")
            print("        -> Les core_chunks ne partagent pas assez de tokens / themes.")
        elif not selection.intent_aligned:
            print("    >>> REFUS DECLENCHE : selection.intent_aligned = False <<<")
            print(f"        -> Le contenu des core_chunks ne contient pas les signaux attendus")
            print(f"           pour l'intent '{intent}'.")
            expected, penalized = selector._intent_signals(intent)  # type: ignore[attr-defined]
            print(f"        signaux attendus  : {sorted(expected)}")
            print(f"        signaux penalises : {sorted(penalized)}")
            for i, chunk in enumerate(selection.core_chunks):
                text_lo = chunk.chunk_text.lower()
                tokens = {tok.lower() for tok in __import__('re').findall(r'\w+', chunk.chunk_text) if len(tok) >= 4}
                has_exp = [s for s in expected if s in text_lo or s in tokens]
                has_pen = [s for s in penalized if s in text_lo or s in tokens]
                article = chunk.metadata.article_ref or "(no article)"
                print(f"        core {i} ({article}): expected_found={has_exp} | penalized_found={has_pen}")
        else:
            print("    >>> AUCUN REFUS DECLENCHE - reponse devrait etre generee.")

        # Verdict final UI (verite absolue).
        view = ui.ask(question_text)
        print(f"\n[5] VERDICT UI")
        print(f"    refusal = {view.refusal}")
        print(f"    intent  = {view.intent}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
