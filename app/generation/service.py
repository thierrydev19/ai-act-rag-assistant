"""Service de génération.

Lot 1: structure et signatures sans logique de génération réelle.
"""

from dataclasses import dataclass

from app.document.models import UserQuestion
from app.retrieval.service import RetrievalResult


@dataclass(frozen=True)
class AnswerPayload:
    """Charge utile de réponse côté application."""

    answer_text: str
    citations: list[str]
    refusal: bool


class GenerationService:
    """Construit une réponse à partir des extraits de retrieval."""

    def generate(self, question: UserQuestion, context: RetrievalResult) -> AnswerPayload:
        """Génère une réponse contrainte par les sources."""
        raise NotImplementedError("Generation non implémentée dans le lot 1.")

