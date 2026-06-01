"""Dependances backend pour l'API web W1."""

from __future__ import annotations

from dataclasses import dataclass
import re

from app.generation.question_mode import classify_question_mode, should_request_business_context
from app.ui.app import DemoCase, UiTurnView, create_showcase_ui

_SECTION_RE = re.compile(
    (
        r"1\.\s*Reponse simple\s*(.*?)\s*"
        r"2\.\s*Ce que cela veut dire pour votre entreprise\s*(.*?)\s*"
        r"3\.\s*Ce qu'il faut verifier\s*(.*?)\s*"
        r"4\.\s*Ce qui reste incertain\s*(.*?)\s*"
        r"5\.\s*Sources\s*(.*?)\s*"
        r"6\.\s*Limites\s*(.*)"
    ),
    re.DOTALL,
)


@dataclass
class ApiBackendService:
    """Facade backend legere reutilisant le moteur existant."""

    _ui: object | None = None

    def ensure_initialized(self) -> None:
        if self._ui is None:
            self._ui = create_showcase_ui()

    def health(self) -> dict[str, str]:
        return {"status": "ok"}

    def demo_cases(self) -> list[DemoCase]:
        self.ensure_initialized()
        return self._ui.demo_cases

    def ask(
        self,
        question: str,
        *,
        usage_case: str | None = None,
        company_role: str | None = None,
        impact_level: str | None = None,
    ) -> dict:
        self.ensure_initialized()
        context_used = {
            "usage_case": usage_case or "non_renseigne",
            "company_role": company_role or "non_renseigne",
            "impact_level": impact_level or "non_renseigne",
        }
        context_needed = self._needs_context(question, context_used)
        context_questions = self._context_questions(context_used) if context_needed else []
        view: UiTurnView = self._ui.ask(
            question,
            context_hint={
                "usage_case": usage_case or "",
                "company_role": company_role or "",
                "impact_level": impact_level or "",
            },
        )
        (
            answer_simple,
            business_impact,
            checks,
            uncertainties,
            sources_from_text,
            limits,
        ) = self._split_answer_sections(view.answer_text)
        sources = view.citations if view.citations else sources_from_text
        return {
            "question": view.question,
            "retrieval_status": view.retrieval_status,
            "retrieval_message": view.retrieval_message,
            "refusal": view.refusal,
            "intent": view.intent,
            "business_case": view.business_case,
            "answer_simple": answer_simple,
            "business_impact": business_impact,
            "checks": checks,
            "uncertainties": uncertainties,
            "sources": sources,
            "limits": limits,
            "context_needed": context_needed,
            "context_questions": context_questions,
            "context_used": context_used,
        }

    def _split_answer_sections(
        self, answer_text: str
    ) -> tuple[str, list[str], list[str], list[str], list[str], list[str]]:
        text = (answer_text or "").strip()
        match = _SECTION_RE.search(text)
        if not match:
            return text, [], [], [], [], []

        answer_simple = match.group(1).strip()
        business_impact = self._to_bullets(match.group(2))
        checks = self._to_bullets(match.group(3))
        uncertainties = self._to_bullets(match.group(4))
        sources = self._to_bullets(match.group(5))
        limits = self._to_bullets(match.group(6))
        return answer_simple, business_impact, checks, uncertainties, sources, limits

    def _to_bullets(self, block: str) -> list[str]:
        lines = [line.strip() for line in (block or "").splitlines()]
        cleaned = [line.removeprefix("-").strip() for line in lines if line.strip()]
        return [line for line in cleaned if line]

    def _needs_context(self, question: str, context_used: dict[str, str]) -> bool:
        question_mode = classify_question_mode(question)
        looks_ambiguous = should_request_business_context(question, question_mode)
        enough_context = all(
            context_used[key] not in {"", "non_renseigne", "je_ne_sais_pas"}
            for key in ("usage_case", "company_role", "impact_level")
        )
        return looks_ambiguous and not enough_context

    def _context_questions(self, context_used: dict[str, str]) -> list[str]:
        questions: list[str] = []
        if context_used["usage_case"] in {"", "non_renseigne", "je_ne_sais_pas"}:
            questions.append("Quel est votre cas d'usage principal ?")
        if context_used["company_role"] in {"", "non_renseigne", "je_ne_sais_pas"}:
            questions.append("Quel est le role principal de votre entreprise ?")
        if context_used["impact_level"] in {"", "non_renseigne", "je_ne_sais_pas"}:
            questions.append("Quel est le niveau d'impact de votre systeme ?")
        return questions[:3]


_backend_singleton = ApiBackendService()


def get_backend_service() -> ApiBackendService:
    return _backend_singleton

