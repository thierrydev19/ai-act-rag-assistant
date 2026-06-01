"""Tests couche question_mode V2."""

from __future__ import annotations

import unittest

from app.generation.question_mode import classify_question_mode
from app.ui.v2_validation import official_v2_questions


class TestQuestionMode(unittest.TestCase):
    def test_official_grid_modes(self) -> None:
        by_qid = {item.qid: item.question for item in official_v2_questions()}
        expected = {
            "Q1": "applicability_gate",
            "Q5": "yes_no_non_automatic",
            "Q6": "yes_no_non_automatic",
            "Q9": "obligation_prioritization",
            "Q17": "role_determination",
            "Q20": "forbidden_compliance_conclusion",
        }
        for qid, mode in expected.items():
            self.assertEqual(classify_question_mode(by_qid[qid]), mode, msg=qid)

    def test_fallback_generic_contextual(self) -> None:
        mode = classify_question_mode("Expliquez le cadre general de l'AI Act pour une PME.")
        self.assertEqual(mode, "generic_contextual")


if __name__ == "__main__":
    unittest.main()
