"""Lance le quality_gate officiel sur les 15 questions canoniques et sauve le
rapport markdown.

Usage:
    python scripts/v3_3_run_quality_gate.py

Sortie :
    docs/cto/lot_v3_3_quality_report.md   (rapport markdown formel)
    + tableau console synthetique pour lecture rapide

Ce script reflete la verite officielle du systeme : c'est le meme jugement que
celui rendu dans la CI / dans le V1 / V2, mais sur l'etat courant V3-3a.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from app.ui.app import create_showcase_ui
from app.ui.quality_gate import (
    default_quality_questions,
    format_report_markdown,
    run_quality_gate,
)


def main() -> int:
    print("Bootstrap UI (ingestion + chunking + indexation)...")
    started = time.perf_counter()
    ui = create_showcase_ui()
    boot = time.perf_counter() - started
    print(f"UI prete en {boot:.1f}s")
    print()

    print("Lancement du quality_gate sur les 15 questions canoniques...")
    started = time.perf_counter()
    report = run_quality_gate(ui=ui, questions=default_quality_questions())
    elapsed = time.perf_counter() - started
    print(f"Quality gate termine en {elapsed:.1f}s")
    print()

    # Synthese console.
    print("=" * 100)
    print(f"DECISION: {report.decision.upper()}")
    print(f"Motif:    {report.decision_reason}")
    print()
    print(f"Taux acceptable:           {report.acceptable_rate:.1%}")
    print(f"Demo sources exploitables: {report.demo_sources_ok}")
    print(f"Refus corrects:            {report.refusal_ok}")
    print(f"Stabilite:                 {report.stable}")
    print(f"Lisibilite PME (format):   {report.understandable_for_sme}")
    print(f"Temps max:                 {report.max_latency_seconds:.3f}s")
    print(f"Temps moyen:               {report.average_latency_seconds:.3f}s")
    print()

    print("Detail par question :")
    print(f"{'Cat':6} {'Att':9} {'Obs':9} {'Resp':10} {'Cit':10} {'Verdict':36} {'Latency':>8}  Question")
    print("-" * 140)
    for r in report.rows:
        print(
            f"{_short(r.expected_status, 6):6} "
            f"{_short(r.expected_status, 9):9} "
            f"{_short(r.observed_status, 9):9} "
            f"{_short(r.response_quality, 10):10} "
            f"{_short(r.citation_quality, 10):10} "
            f"{_short(r.verdict, 36):36} "
            f"{r.latency_seconds:>7.3f}s  "
            f"{r.question[:60]}"
        )
    print()

    # Sauvegarde markdown.
    report_path = _REPO_ROOT / "docs" / "cto" / "lot_v3_3_quality_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    md = format_report_markdown(report)
    # Ajouter un en-tete contextuel V3-3.
    header = (
        "# Lot V3-3a — Rapport Quality Gate officiel sur grille canonique 15 questions\n\n"
        f"Etat : V3-3a (sentence-transformers + retrieval recalibre min_combined_score=0.385)\n\n"
        f"Corpus : AI Act FR officiel (UE 2024/1689), 144 pages, 230 chunks\n\n"
        "---\n\n"
    )
    report_path.write_text(header + md, encoding="utf-8")
    print(f"Rapport ecrit dans: {report_path}")
    return 0


def _short(s: str, n: int) -> str:
    return (s or "")[:n]


if __name__ == "__main__":
    raise SystemExit(main())
