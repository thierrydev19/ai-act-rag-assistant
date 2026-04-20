"""Service de generation contrainte par sources (lot 7)."""

from __future__ import annotations

from dataclasses import dataclass
import re

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


class GenerationService:
    """Construit une reponse professionnelle strictement bornee aux sources."""

    def __init__(self, *, max_citations: int = 3) -> None:
        if max_citations <= 0:
            raise ValueError("max_citations doit etre strictement positif.")
        self._max_citations = max_citations

    def generate(self, question: UserQuestion, context: RetrievalResult) -> AnswerPayload:
        """Genere une reponse contrainte avec citations ou refus explicite."""
        if not context.is_sufficient or not context.chunks:
            refusal = self._build_refusal(context_message=context.message)
            return AnswerPayload(
                answer_text=refusal,
                citations=[],
                refusal=True,
            )

        citations = [self._format_citation(c) for c in context.chunks[: self._max_citations]]
        answer_text = self._build_grounded_answer(question=question, context=context, citations=citations)
        return AnswerPayload(
            answer_text=answer_text,
            citations=citations,
            refusal=False,
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
            "1. Reponse simple\n2. Ce qu'il faut verifier\n3. Sources\n4. Limites\n\n"
            f"Question: {question.text.strip()}\n\n"
            f"Extraits:\n{chunks_block}"
        )

    def _build_grounded_answer(
        self,
        *,
        question: UserQuestion,
        context: RetrievalResult,
        citations: list[str],
    ) -> str:
        highlights = self._extract_highlights(question.text, context)
        main = (
            "Les extraits retrouves indiquent les points suivants:"
            if highlights
            else "Les extraits retrouves apportent des elements partiels sur votre question."
        )
        bullet_text = "\n".join(f"- {item}" for item in highlights) if highlights else "- Les extraits ne couvrent qu'une partie du sujet."
        checks = (
            "- Verifier que votre cas concret correspond bien au perimetre des articles cites.\n"
            "- Confirmer les obligations exactes selon le contexte de votre activite."
        )
        sources = "\n".join(f"- {c}" for c in citations)
        limits = (
            "- Cette reponse est fournie a titre informatif et ne constitue pas un avis juridique definitif.\n"
            "- Le corpus charge peut etre insuffisant pour conclure sur tous les cas particuliers."
        )
        return (
            "1. Reponse simple\n"
            f"{main}\n{bullet_text}\n\n"
            "2. Ce qu'il faut verifier\n"
            f"{checks}\n\n"
            "3. Sources\n"
            f"{sources}\n\n"
            "4. Limites\n"
            f"{limits}"
        )

    def _build_refusal(self, *, context_message: str) -> str:
        return (
            "1. Reponse simple\n"
            "Je ne peux pas conclure de maniere fiable a partir du corpus charge pour cette question.\n\n"
            "2. Ce qu'il faut verifier\n"
            f"- Cause principale: {context_message}\n"
            "- Reformuler la question ou enrichir le corpus/documentation avant toute conclusion.\n\n"
            "3. Sources\n"
            "- Aucune source suffisamment pertinente n'a pu etre retenue.\n\n"
            "4. Limites\n"
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

