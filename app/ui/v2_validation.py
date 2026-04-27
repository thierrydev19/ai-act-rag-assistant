"""Validation finale V2 basee sur la grille officielle PME (20 questions)."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from app.ui.app import ShowcaseUI, create_showcase_ui


@dataclass(frozen=True)
class V2Question:
    qid: str
    question: str
    intent: str
    demo_priority: bool
    expected_refusal: bool


@dataclass(frozen=True)
class V2ScoreRow:
    qid: str
    question: str
    expected_intent: str
    observed_intent: str
    refusal: bool
    score: int  # 0,1,2
    has_sources: bool
    notes: str


@dataclass(frozen=True)
class V2ValidationReport:
    rows: list[V2ScoreRow]
    success_rate: float
    demo_sources_ok: bool
    demo_priorities_ok: bool
    refusal_quality_ok: bool
    decision: str  # cloturee | non_cloturee
    decision_reason: str


def official_v2_questions() -> list[V2Question]:
    """Questions figees depuis docs/cto/17_GRILLE_V2_QUESTIONS_PME_VALIDATION.md."""
    return [
        V2Question("Q1", "Nous sommes une PME qui utilise ChatGPT pour rediger des emails et des comptes rendus internes. Est-ce que l'AI Act nous concerne ?", "applicability_perimetre", True, False),
        V2Question("Q2", "Nous utilisons un outil d'IA achete chez un editeur, mais nous ne developpons rien nous-memes. Est-ce que nous avons quand meme des obligations ?", "applicability_perimetre", False, False),
        V2Question("Q3", "Nous testons une IA uniquement en interne, sans l'utiliser encore avec nos clients. Est-ce deja dans le perimetre de l'AI Act ?", "applicability_perimetre", False, False),
        V2Question("Q4", "Nous sommes une PME francaise sans activite hors Europe. Est-ce que l'AI Act peut quand meme s'appliquer a nous ?", "applicability_perimetre", False, False),
        V2Question("Q5", "Nous utilisons une IA pour trier des CV avant entretien. Est-ce que cela peut etre considere comme un systeme a haut risque ?", "qualification_systeme", True, False),
        V2Question("Q6", "Nous avons un chatbot sur notre site web qui repond aux questions clients. Est-ce automatiquement un systeme a haut risque ?", "qualification_systeme", True, False),
        V2Question("Q7", "Nous utilisons une IA pour aider un commercial a prioriser ses prospects. Est-ce que ce type d'usage entre dans une categorie sensible de l'AI Act ?", "qualification_systeme", False, False),
        V2Question("Q8", "Nous voulons utiliser une IA generative pour produire des fiches produits visibles par nos clients. Quel est le sujet principal a regarder dans l'AI Act ?", "qualification_systeme", False, False),
        V2Question("Q9", "Si notre usage d'IA entre dans le champ de l'AI Act, qu'est-ce qu'un dirigeant PME doit verifier en premier ?", "obligations_entreprise", False, False),
        V2Question("Q10", "Nous utilisons une IA dans un processus RH. Quelles obligations concretes peuvent nous concerner en tant qu'entreprise utilisatrice ?", "obligations_entreprise", False, False),
        V2Question("Q11", "Si nous achetons une solution d'IA a un prestataire, que devons-nous exiger ou verifier avant de l'utiliser ?", "obligations_entreprise", True, False),
        V2Question("Q12", "Quels elements devons-nous documenter en interne pour montrer que nous utilisons une IA de maniere serieuse et maitrisee ?", "documentation_preuves", False, False),
        V2Question("Q13", "Devons-nous informer nos clients lorsqu'ils interagissent avec une IA ?", "transparence_information", False, False),
        V2Question("Q14", "Devons-nous informer nos salaries si une IA intervient dans certaines decisions ou recommandations internes ?", "transparence_information", False, False),
        V2Question("Q15", "Quand une IA genere un contenu visible par un tiers, qu'est-ce que l'entreprise doit verifier sur le plan de la transparence ?", "transparence_information", False, False),
        V2Question("Q16", "Quels types de preuves ou de documents une PME devrait-elle conserver en priorite autour de ses usages IA ?", "documentation_preuves", False, False),
        V2Question("Q17", "Comment savoir si notre PME est plutot fournisseur, deployeur ou simple utilisatrice au sens de l'AI Act ?", "role_entreprise", False, False),
        V2Question("Q18", "Nous faisons developper une IA sur mesure par un prestataire externe pour nos propres besoins. Quel est probablement notre role et que faut-il verifier ?", "role_entreprise", False, False),
        V2Question("Q19", "Nous integrons une brique d'IA tierce dans notre propre service vendu a des clients. Est-ce que notre role change au regard de l'AI Act ?", "role_entreprise", False, False),
        V2Question("Q20", "Pouvez-vous me dire si mon entreprise est conforme a l'AI Act aujourd'hui, oui ou non ?", "limites_conclusion", True, True),
    ]


def run_v2_validation(*, ui: ShowcaseUI | None = None) -> V2ValidationReport:
    effective_ui = ui or create_showcase_ui()
    rows: list[V2ScoreRow] = []
    for item in official_v2_questions():
        view = effective_ui.ask(item.question)
        row = _score_question(item, view)
        rows.append(row)
    success = [row for row in rows if row.score in (1, 2)]
    success_rate = len(success) / len(rows) if rows else 0.0

    demos = [row for row in rows if row.qid in {"Q1", "Q5", "Q6", "Q11", "Q20"}]
    demo_sources_ok = all(row.refusal or row.has_sources for row in demos)
    demo_priorities_ok = all(row.score in (1, 2) for row in demos)
    refusal_rows = [row for row in rows if row.expected_intent == "limites_conclusion"]
    refusal_quality_ok = all(row.refusal for row in refusal_rows)

    if success_rate >= 0.8 and demo_sources_ok and demo_priorities_ok and refusal_quality_ok:
        decision = "cloturee"
        reason = "Seuils V2 atteints: taux >=80%, demos prioritaires maitrisees, refus propre."
    else:
        decision = "non_cloturee"
        reason = "Au moins un seuil critique V2 n'est pas atteint sur la grille officielle."
    return V2ValidationReport(
        rows=rows,
        success_rate=success_rate,
        demo_sources_ok=demo_sources_ok,
        demo_priorities_ok=demo_priorities_ok,
        refusal_quality_ok=refusal_quality_ok,
        decision=decision,
        decision_reason=reason,
    )


def format_v2_validation_report(report: V2ValidationReport) -> str:
    scores = [row.score for row in report.rows]
    avg_score = mean(scores) if scores else 0.0
    lines = [
        "# Rapport final validation V2",
        "",
        "- Reference officielle: docs/cto/17_GRILLE_V2_QUESTIONS_PME_VALIDATION.md",
        f"- Questions evaluees: {len(report.rows)}",
        f"- Taux reussite (score 1 ou 2): {report.success_rate:.1%}",
        f"- Score moyen: {avg_score:.2f}/2",
        f"- Demos prioritaires (Q1,Q5,Q6,Q11,Q20): {report.demo_priorities_ok}",
        f"- Sources exploitables sur demos: {report.demo_sources_ok}",
        f"- Refus honnetes maitrises: {report.refusal_quality_ok}",
        f"- Decision finale V2: **{report.decision}**",
        f"- Motif: {report.decision_reason}",
        "",
        "## Detail par question",
        "",
        "| QID | Intent attendu | Intent observe | Refus | Score | Sources | Notes |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in report.rows:
        lines.append(
            f"| {row.qid} | {row.expected_intent} | {row.observed_intent} | "
            f"{row.refusal} | {row.score} | {row.has_sources} | {row.notes} |"
        )
    return "\n".join(lines)


def _score_question(item: V2Question, view) -> V2ScoreRow:
    has_sources = len(view.citations) > 0
    sections_ok = all(
        marker in view.answer_text
        for marker in (
            "1. Reponse simple",
            "2. Ce que cela veut dire pour votre entreprise",
            "3. Ce qu'il faut verifier",
            "4. Ce qui reste incertain",
            "5. Sources",
            "6. Limites",
        )
    )
    intent_match = (view.intent == item.intent) or (item.intent == "limites_conclusion" and view.refusal)
    if item.expected_refusal:
        score = 2 if view.refusal else 0
        notes = "Refus attendu." if view.refusal else "Refus attendu mais non produit."
    else:
        if not sections_ok:
            score = 0
            notes = "Structure 6 blocs incomplete."
        elif view.refusal:
            score = 1
            notes = "Refus prudent sur question potentiellement ambigue."
        elif intent_match and has_sources:
            score = 2
            notes = "Reponse contextualisee, sourcee et prudente."
        elif has_sources:
            score = 1
            notes = "Reponse partielle acceptable mais alignement intent perfectible."
        else:
            score = 0
            notes = "Absence de sources exploitables."
    return V2ScoreRow(
        qid=item.qid,
        question=item.question,
        expected_intent=item.intent,
        observed_intent=view.intent,
        refusal=view.refusal,
        score=score,
        has_sources=has_sources,
        notes=notes,
    )

