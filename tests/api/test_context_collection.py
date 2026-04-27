"""Tests lot 6 - collecte minimale de contexte metier."""

from __future__ import annotations

import unittest

from app.api.dependencies import ApiBackendService


class TestContextCollection(unittest.TestCase):
    def setUp(self) -> None:
        self.backend = ApiBackendService()

    def test_context_questions_trigger_only_when_useful(self) -> None:
        context_used = {
            "usage_case": "non_renseigne",
            "company_role": "non_renseigne",
            "impact_level": "non_renseigne",
        }
        needed = self.backend._needs_context(
            "Quelles obligations avons-nous en tant qu'entreprise ?",
            context_used,
        )
        self.assertTrue(needed)
        questions = self.backend._context_questions(context_used)
        self.assertGreaterEqual(len(questions), 1)
        self.assertLessEqual(len(questions), 3)

    def test_context_questions_not_for_precise_question(self) -> None:
        context_used = {
            "usage_case": "non_renseigne",
            "company_role": "non_renseigne",
            "impact_level": "non_renseigne",
        }
        needed = self.backend._needs_context(
            "Quel est le regime fiscal mondial de l'IA ?",
            context_used,
        )
        self.assertFalse(needed)

    def test_context_questions_stop_when_context_is_complete(self) -> None:
        context_used = {
            "usage_case": "service_client",
            "company_role": "fournisseur",
            "impact_level": "influence_une_decision",
        }
        needed = self.backend._needs_context(
            "Quelles obligations avons-nous en tant qu'entreprise ?",
            context_used,
        )
        self.assertFalse(needed)


if __name__ == "__main__":
    unittest.main()

