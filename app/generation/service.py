"""Service de generation contrainte par sources (lot 7)."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal

from app.document.models import UserQuestion
from app.retrieval.service import RetrievalResult
from app.logging.logger import get_logger

logger = get_logger(__name__)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_RE = re.compile(r"\w+", re.UNICODE)


@dataclass(frozen=True)
class AnswerPayload:
    """Charge utile de réponse côté application."""

    answer_text: str
    citations: list[str]
    refusal: bool
    intent: str


class GenerationService:
    """Construit une reponse professionnelle strictement bornee aux sources."""

    def __init__(self, *, max_citations: int = 3) -> None:
        if max_citations <= 0:
            raise ValueError("max_citations doit etre strictement positif.")
        self._max_citations = max_citations

    def generate(self, question: UserQuestion, context: RetrievalResult) -> AnswerPayload:
        """Genere une reponse contrainte avec citations ou refus explicite."""
        intent = self._classify_intent(question.text)
        if self._is_out_of_scope_question(question.text):
            refusal = self._build_refusal(
                context_message=(
                    "Question hors perimetre documentaire (demande de conseil strategique "
                    "ou d'avis juridique definitif)."
                )
            )
            return AnswerPayload(
                answer_text=refusal,
                citations=[],
                refusal=True,
                intent="limites_conclusion",
            )
        if not context.is_sufficient or not context.chunks:
            refusal = self._build_refusal(context_message=context.message)
            return AnswerPayload(
                answer_text=refusal,
                citations=[],
                refusal=True,
                intent="limites_conclusion",
            )

        citations = [self._format_citation(c) for c in context.chunks[: self._max_citations]]
        answer_text = self._build_grounded_answer(
            question=question,
            context=context,
            citations=citations,
            intent=intent,
        )
        return AnswerPayload(
            answer_text=answer_text,
            citations=citations,
            refusal=False,
            intent=intent,
        )

    def build_constrained_prompt(self, question: UserQuestion, context: RetrievalResult) -> str:
        """Construit un prompt strictement borne aux extraits retrouves."""
        chunks = context.chunks[: self._max_citations]
        if not chunks:
            chunks_block = "Aucun extrait."
        else:
            lines: list[str] = []
            for idx, chunk in enumerate(chunks, start=1):
                lines.append(f"[EXTRAIT {idx}] {self._format_citation(chunk)}")
                lines.append(chunk.chunk_text.strip())
            chunks_block = "\n".join(lines)
        return (
            "Tu reponds uniquement avec les informations presentes dans les extraits ci-dessous.\n"
            "Interdits: invention, extrapolation juridique definitive, ajout de source externe.\n"
            "Si information insuffisante: refuser explicitement.\n"
            "Format impose:\n"
            "1. Reponse simple\n"
            "2. Ce que cela veut dire pour votre entreprise\n"
            "3. Ce qu'il faut verifier\n"
            "4. Ce qui reste incertain\n"
            "5. Sources\n"
            "6. Limites\n\n"
            f"Question: {question.text.strip()}\n\n"
            f"Extraits:\n{chunks_block}"
        )

    def _build_grounded_answer(
        self,
        *,
        question: UserQuestion,
        context: RetrievalResult,
        citations: list[str],
        intent: str,
    ) -> str:
        highlights = self._extract_highlights(question.text, context)
        answer_simple = self._build_answer_simple(highlights)
        business_impact = self._build_business_impact(intent=intent, highlights=highlights)
        checks = (
            "- Verifier que votre cas concret correspond bien au perimetre des articles cites.\n"
            "- Confirmer les obligations exactes selon le contexte de votre activite."
        )
        uncertainties = (
            "- Les extraits recuperes peuvent ne pas couvrir tous les details de votre situation.\n"
            "- Une qualification finale depend de faits operationnels qui ne figurent pas dans le corpus."
        )
        sources = "\n".join(f"- {c}" for c in citations)
        limits = (
            "- Cette reponse est fournie a titre informatif et ne constitue pas un avis juridique definitif.\n"
            "- Le corpus charge peut etre insuffisant pour conclure sur tous les cas particuliers."
        )
        return (
            "1. Reponse simple\n"
            f"{answer_simple}\n\n"
            "2. Ce que cela veut dire pour votre entreprise\n"
            f"{business_impact}\n\n"
            "3. Ce qu'il faut verifier\n"
            f"{checks}\n\n"
            "4. Ce qui reste incertain\n"
            f"{uncertainties}\n\n"
            "5. Sources\n"
            f"{sources}\n\n"
            "6. Limites\n"
            f"{limits}"
        )

    def _build_refusal(self, *, context_message: str) -> str:
        return (
            "1. Reponse simple\n"
            "Je ne peux pas conclure de maniere fiable a partir du corpus charge pour cette question.\n\n"
            "2. Ce que cela veut dire pour votre entreprise\n"
            "- Vous ne devez pas prendre une decision de conformite uniquement sur cette base.\n\n"
            "3. Ce qu'il faut verifier\n"
            f"- Cause principale: {context_message}\n"
            "- Reformuler la question ou enrichir le corpus/documentation avant toute conclusion.\n\n"
            "4. Ce qui reste incertain\n"
            "- Le corpus actuel ne permet pas d'etablir une position fiable pour votre cas.\n\n"
            "5. Sources\n"
            "- Aucune source suffisamment pertinente n'a pu etre retenue.\n\n"
            "6. Limites\n"
            "- Cette reponse ne constitue pas un avis juridique definitif.\n"
            "- Sans base documentaire suffisante, toute conclusion serait speculative."
        )

    def _extract_highlights(self, question_text: str, context: RetrievalResult) -> list[str]:
        keywords = {
            token.lower()
            for token in _WORD_RE.findall(question_text or "")
            if len(token) >= 4
        }
        highlights: list[str] = []
        for chunk in context.chunks[: self._max_citations]:
            sentences = _SENTENCE_SPLIT_RE.split(chunk.chunk_text.strip())
            chosen = None
            for sentence in sentences:
                sentence_tokens = {t.lower() for t in _WORD_RE.findall(sentence)}
                if keywords and sentence_tokens.intersection(keywords):
                    chosen = sentence.strip()
                    break
            if chosen is None and sentences:
                chosen = sentences[0].strip()
            if chosen:
                citation = self._format_citation(chunk)
                highlights.append(f"{chosen} ({citation})")
        return highlights

    def _format_citation(self, chunk) -> str:
        meta = chunk.metadata
        page = self._format_page(meta.page_number)
        if meta.article_ref and meta.section_ref:
            return f"AI Act - {meta.article_ref} - Section {meta.section_ref} - page {page}"
        if meta.article_ref:
            return f"AI Act - {meta.article_ref} - page {page}"
        if meta.section_ref:
            return f"AI Act - Section {meta.section_ref} - page {page}"
        return f"AI Act - page {page}"

    def _format_page(self, page_number: int | tuple[int, int]) -> str:
        if isinstance(page_number, int):
            return str(page_number)
        return f"{page_number[0]}-{page_number[1]}"

    def _is_out_of_scope_question(self, question_text: str) -> bool:
        text = (question_text or "").lower()
        out_of_scope_markers = (
            "avis juridique definitif",
            "strategie commerciale",
            "meilleur choix de fournisseur",
            "hors ai act",
            "regime fiscal",
            "fiscalite",
        )
        return any(marker in text for marker in out_of_scope_markers)

    def _classify_intent(
        self, question_text: str
    ) -> Literal[
        "applicability_perimetre",
        "qualification_systeme",
        "obligations_entreprise",
        "transparence_information",
        "documentation_preuves",
        "role_entreprise",
        "limites_conclusion",
    ]:
        text = (question_text or "").lower()
        if any(word in text for word in ("applicable", "perimetre", "concerne")):
            return "applicability_perimetre"
        if any(word in text for word in ("definition", "qualif", "systeme ia")):
            return "qualification_systeme"
        if any(word in text for word in ("transparence", "informer", "information")):
            return "transparence_information"
        if any(word in text for word in ("obligation", "doit", "conformite")):
            return "obligations_entreprise"
        if any(word in text for word in ("documentation", "preuve", "trace")):
            return "documentation_preuves"
        if any(word in text for word in ("fournisseur", "deployeur", "importateur", "role")):
            return "role_entreprise"
        return "limites_conclusion"

    def _build_answer_simple(self, highlights: list[str]) -> str:
        if not highlights:
            return "Les extraits retrouves apportent des elements partiels sur votre question."
        return "Les extraits retrouves indiquent les points suivants:\n" + "\n".join(
            f"- {item}" for item in highlights
        )

    def _build_business_impact(self, *, intent: str, highlights: list[str]) -> str:
        if not highlights:
            return "- Vous devez traiter ce sujet comme un point a clarifier avant toute decision operationnelle."
        by_intent = {
            "applicability_perimetre": "- Cela aide a determiner si votre activite entre dans le champ du reglement et si des obligations s'appliquent.",
            "qualification_systeme": "- Cela permet d'orienter la qualification initiale de votre systeme, sans conclure definitivement.",
            "obligations_entreprise": "- Cela indique des actions de conformite potentielles a organiser dans votre entreprise.",
            "transparence_information": "- Cela implique de preparer des informations claires pour les utilisateurs et parties prenantes.",
            "documentation_preuves": "- Cela implique de structurer des preuves documentaires pour justifier vos choix et controles.",
            "role_entreprise": "- Cela aide a preciser vos responsabilites selon votre role dans la chaine de valeur IA.",
            "limites_conclusion": "- Cela donne une orientation utile, mais insuffisante pour une decision definitive sans verifications complementaires.",
        }
        return by_intent.get(intent, by_intent["limites_conclusion"])

