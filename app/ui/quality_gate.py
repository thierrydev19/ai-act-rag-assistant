"""Validation lot 10 : grille qualite MVP sur scenarios de demonstration."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
import time
import re
import unicodedata

from app.ui.app import DemoCase, ShowcaseUI, create_showcase_ui, default_demo_cases

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


@dataclass(frozen=True)
class QualityQuestion:
    """Question de validation avec statut attendu et mots-clefs de controle."""

    question: str
    expected_status: str  # positive | limit | refusal
    keywords: tuple[str, ...]
    category: str  # positive | limit | refusal


@dataclass(frozen=True)
class QualityEvaluationRow:
    """Resultat evalue pour une question unique."""

    question: str
    expected_status: str
    observed_status: str
    response_quality: str
    citation_quality: str
    verdict: str  # correct | partiellement correct acceptable | insuffisant
    remarks: str
    latency_seconds: float


@dataclass(frozen=True)
class QualityGateReport:
    """Synthese de passage de la grille MVP."""

    rows: list[QualityEvaluationRow]
    acceptable_rate: float
    demo_sources_ok: bool
    refusal_ok: bool
    stable: bool
    max_latency_seconds: float
    average_latency_seconds: float
    understandable_for_sme: bool
    decision: str  # montrable | non montrable
    decision_reason: str


def format_report_markdown(report: QualityGateReport) -> str:
    """Formate le rapport de grille qualite en markdown lisible."""
    lines = [
        "# Lot 10 - Grille qualite MVP",
        "",
        f"- Decision: **{report.decision}**",
        f"- Motif: {report.decision_reason}",
        f"- Taux acceptable: {report.acceptable_rate:.1%}",
        f"- Demo sources exploitables: {report.demo_sources_ok}",
        f"- Refus corrects: {report.refusal_ok}",
        f"- Stabilite: {report.stable}",
        f"- Temps max (s): {report.max_latency_seconds:.3f}",
        f"- Temps moyen (s): {report.average_latency_seconds:.3f}",
        f"- Lisibilite PME (format): {report.understandable_for_sme}",
        "",
        "## Evaluation detaillee",
        "",
        "| Question | Statut attendu | Statut observe | Qualite reponse | Qualite citations | Verdict | Remarques | Latence (s) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in report.rows:
        lines.append(
            f"| {row.question} | {row.expected_status} | {row.observed_status} | "
            f"{row.response_quality} | {row.citation_quality} | {row.verdict} | "
            f"{row.remarks} | {row.latency_seconds:.3f} |"
        )
    return "\n".join(lines)


def default_quality_questions() -> list[QualityQuestion]:
    """Jeu de 15 questions: 8 positives, 3 limites, 4 refus attendus."""
    demo_map: dict[str, DemoCase] = {c.case_id: c for c in default_demo_cases()}
    return [
        QualityQuestion(
            question=demo_map["transparence"].question,
            expected_status="positive",
            keywords=("transparence", "informations"),
            category="positive",
        ),
        QualityQuestion(
            question=demo_map["sanctions"].question,
            expected_status="positive",
            keywords=("sanctions", "administratives"),
            category="positive",
        ),
        QualityQuestion(
            question=demo_map["definition"].question,
            expected_status="positive",
            keywords=("definition", "systeme"),
            category="positive",
        ),
        QualityQuestion(
            question="Quelles obligations existent pour les systemes IA a haut risque ?",
            expected_status="positive",
            keywords=("haut", "risque", "obligations"),
            category="positive",
        ),
        QualityQuestion(
            question="Que faut-il verifier avant de mettre un systeme IA sur le marche ?",
            expected_status="positive",
            keywords=("verifier", "marche", "obligations"),
            category="positive",
        ),
        QualityQuestion(
            question="Que prevoit le texte pour la surveillance des systemes IA ?",
            expected_status="positive",
            keywords=("surveillance", "systemes"),
            category="positive",
        ),
        QualityQuestion(
            question="Que dit l'AI Act sur les voies de recours ?",
            expected_status="positive",
            keywords=("recours", "reclamation"),
            category="positive",
        ),
        QualityQuestion(
            question="Quels points de conformite sont attendus pour les fournisseurs ?",
            expected_status="positive",
            keywords=("conformite", "fournisseurs"),
            category="positive",
        ),
        QualityQuestion(
            question="Quelles obligations pour les importateurs de systemes IA ?",
            expected_status="limit",
            keywords=("importateurs", "obligations"),
            category="limit",
        ),
        QualityQuestion(
            question="Que dit le texte sur les obligations des deployeurs ?",
            expected_status="limit",
            keywords=("deployeurs", "obligations"),
            category="limit",
        ),
        QualityQuestion(
            question="Comment s'articule la gouvernance europeenne de l'IA ?",
            expected_status="limit",
            keywords=("gouvernance", "europeenne"),
            category="limit",
        ),
        QualityQuestion(
            question=demo_map["hors_perimetre"].question,
            expected_status="refusal",
            keywords=("fiscal", "mondial"),
            category="refusal",
        ),
        QualityQuestion(
            question="Peux-tu donner un avis juridique definitif pour mon entreprise ?",
            expected_status="refusal",
            keywords=("avis", "juridique"),
            category="refusal",
        ),
        QualityQuestion(
            question="Quels sont les regles IA en Asie hors AI Act ?",
            expected_status="refusal",
            keywords=("asie", "hors"),
            category="refusal",
        ),
        QualityQuestion(
            question="Quel est le meilleur choix de fournisseur IA pour ma strategie commerciale ?",
            expected_status="refusal",
            keywords=("strategie", "commerciale"),
            category="refusal",
        ),
    ]


def run_quality_gate(
    *,
    ui: ShowcaseUI | None = None,
    questions: list[QualityQuestion] | None = None,
) -> QualityGateReport:
    """Execute la grille qualite lot 10 sur un corpus indexe."""
    effective_ui = ui or create_showcase_ui()
    effective_questions = questions or default_quality_questions()
    rows: list[QualityEvaluationRow] = []
    for item in effective_questions:
        started = time.perf_counter()
        view = effective_ui.ask(item.question)
        latency = time.perf_counter() - started
        row = _evaluate_question(item, view, latency_seconds=latency)
        rows.append(row)
    return _build_report(rows=rows, demo_cases=effective_ui.demo_cases)


def _evaluate_question(
    item: QualityQuestion,
    view,
    *,
    latency_seconds: float,
) -> QualityEvaluationRow:
    observed_status = "refusal" if view.refusal else "positive"
    response_quality = _response_quality(view.answer_text)
    citation_quality = _citation_quality(view.citations, refusal=view.refusal)
    keyword_hits = _count_keyword_hits(item.keywords, view.answer_text)

    if item.expected_status == "refusal":
        verdict = "correct" if view.refusal else "insuffisant"
    elif view.refusal:
        verdict = "partiellement correct acceptable" if item.expected_status == "limit" else "insuffisant"
    elif citation_quality == "faible":
        verdict = "insuffisant"
    elif keyword_hits >= 1:
        verdict = "correct"
    else:
        verdict = "partiellement correct acceptable" if item.expected_status == "limit" else "insuffisant"

    remarks = (
        f"retrieval={view.retrieval_status}; citations={len(view.citations)}; keyword_hits={keyword_hits}"
    )
    return QualityEvaluationRow(
        question=item.question,
        expected_status=item.expected_status,
        observed_status=observed_status,
        response_quality=response_quality,
        citation_quality=citation_quality,
        verdict=verdict,
        remarks=remarks,
        latency_seconds=latency_seconds,
    )


def _count_keyword_hits(keywords: tuple[str, ...], answer_text: str) -> int:
    text_tokens = {_light_stem(tok) for tok in _extract_tokens(answer_text)}
    hits = 0
    for keyword in keywords:
        key_tokens = [_light_stem(tok) for tok in _extract_tokens(keyword)]
        if not key_tokens:
            continue
        if all(token in text_tokens for token in key_tokens):
            hits += 1
    return hits


def _extract_tokens(text: str) -> list[str]:
    normalized = (
        unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    )
    return [tok.lower() for tok in _TOKEN_RE.findall(normalized)]


def _light_stem(token: str) -> str:
    if len(token) <= 4:
        return token
    for suffix in (
        "ements",
        "ement",
        "ations",
        "ation",
        "teurs",
        "teur",
        "ments",
        "ment",
        "ions",
        "ion",
        "iques",
        "ique",
        "istes",
        "iste",
        "eurs",
        "eaux",
        "eau",
        "aux",
        "es",
        "s",
    ):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            return token[: -len(suffix)]
    return token


def _response_quality(answer_text: str) -> str:
    required_sections = (
        "1. Reponse simple",
        "2. Ce que cela veut dire pour votre entreprise",
        "3. Ce qu'il faut verifier",
        "4. Ce qui reste incertain",
        "5. Sources",
        "6. Limites",
    )
    present = sum(1 for marker in required_sections if marker in answer_text)
    if present == len(required_sections):
        return "bonne"
    if present >= 2:
        return "moyenne"
    return "faible"


def _citation_quality(citations: list[str], *, refusal: bool) -> str:
    if refusal:
        return "n/a"
    if not citations:
        return "faible"
    if all(citation.startswith("AI Act - ") and "page " in citation for citation in citations):
        return "bonne"
    return "moyenne"


def _build_report(rows: list[QualityEvaluationRow], demo_cases: list[DemoCase]) -> QualityGateReport:
    acceptable = sum(
        1 for row in rows if row.verdict in ("correct", "partiellement correct acceptable")
    )
    acceptable_rate = acceptable / len(rows) if rows else 0.0
    max_latency = max((row.latency_seconds for row in rows), default=0.0)
    avg_latency = mean([row.latency_seconds for row in rows]) if rows else 0.0
    stable = all(row.observed_status in ("positive", "refusal") for row in rows)
    refusal_rows = [row for row in rows if row.expected_status == "refusal"]
    refusal_ok = all(row.observed_status == "refusal" for row in refusal_rows)
    demo_questions = {case.question for case in demo_cases}
    demo_rows = [row for row in rows if row.question in demo_questions]
    demo_sources_ok = all(
        (row.observed_status == "refusal") or (row.citation_quality == "bonne")
        for row in demo_rows
    )
    understandable_for_sme = all(row.response_quality in ("bonne", "moyenne") for row in rows)

    if (
        acceptable_rate >= 0.8
        and demo_sources_ok
        and refusal_ok
        and stable
        and max_latency < 10.0
        and understandable_for_sme
    ):
        decision = "montrable"
        reason = "La grille lot 10 est satisfaite sur les criteres minimums."
    else:
        decision = "non montrable"
        reason = "Au moins un critere critique lot 10 n'est pas atteint."

    return QualityGateReport(
        rows=rows,
        acceptable_rate=acceptable_rate,
        demo_sources_ok=demo_sources_ok,
        refusal_ok=refusal_ok,
        stable=stable,
        max_latency_seconds=max_latency,
        average_latency_seconds=avg_latency,
        understandable_for_sme=understandable_for_sme,
        decision=decision,
        decision_reason=reason,
    )

