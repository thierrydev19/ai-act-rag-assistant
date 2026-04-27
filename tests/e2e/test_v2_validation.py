"""Tests lot 6 - validation finale V2 sur grille officielle."""

from __future__ import annotations

import unittest
import tempfile

from app.document.models import DocumentChunk, DocumentMetadata
from app.ui.app import create_showcase_ui_from_chunks
from app.ui.app import UiTurnView
from app.ui.v2_validation import (
    format_v2_validation_report,
    official_v2_questions,
    run_v2_validation,
)


class _FakeUi:
    def ask(self, question: str) -> UiTurnView:
        text = (
            "1. Reponse simple\n"
            "Reponse test.\n\n"
            "2. Ce que cela veut dire pour votre entreprise\n"
            "- Impact test.\n\n"
            "3. Ce qu'il faut verifier\n"
            "- Verification test.\n\n"
            "4. Ce qui reste incertain\n"
            "- Incertitude test.\n\n"
            "5. Sources\n"
            "- AI Act - Article 13 - page 52\n\n"
            "6. Limites\n"
            "- Limite test."
        )
        q = question.lower()
        if "conforme a l'ai act aujourd'hui, oui ou non" in q:
            return UiTurnView(
                question=question,
                answer_text=(
                    "1. Reponse simple\nJe ne peux pas conclure de maniere fiable a partir du corpus charge pour cette question.\n\n"
                    "2. Ce que cela veut dire pour votre entreprise\n- Vous ne devez pas prendre une decision definitive sur cette base.\n\n"
                    "3. Ce qu'il faut verifier\n- Cause principale: demande de conclusion definitive.\n\n"
                    "4. Ce qui reste incertain\n- Le corpus ne permet pas d'etablir une conclusion binaire.\n\n"
                    "5. Sources\n- Aucune source suffisamment pertinente n'a pu etre retenue.\n\n"
                    "6. Limites\n- Cette reponse ne constitue pas un avis juridique definitif."
                ),
                citations=[],
                refusal=True,
                intent="limites_conclusion",
                business_case="generic",
                retrieval_status="insufficient",
                retrieval_message="insufficient",
            )
        intent = "transparence_information"
        if "haut risque" in q or "chatbot" in q or "qualifier" in q:
            intent = "qualification_systeme"
        if "obligations" in q and "entreprise" in q:
            intent = "obligations_entreprise"
        if "documents" in q or "preuves" in q:
            intent = "documentation_preuves"
        if "role" in q or "fournisseur" in q or "deployeur" in q:
            intent = "role_entreprise"
        if "concerne" in q or "perimetre" in q:
            intent = "applicability_perimetre"
        return UiTurnView(
            question=question,
            answer_text=text,
            citations=["AI Act - Article 13 - page 52"],
            refusal=False,
            intent=intent,
            business_case="generic",
            retrieval_status="sufficient",
            retrieval_message="ok",
        )


class TestV2Validation(unittest.TestCase):
    def test_official_grid_has_20_questions_and_5_priorities(self) -> None:
        questions = official_v2_questions()
        self.assertEqual(len(questions), 20)
        priorities = [q for q in questions if q.demo_priority]
        self.assertEqual(len(priorities), 5)
        self.assertEqual([q.qid for q in priorities], ["Q1", "Q5", "Q6", "Q11", "Q20"])

    def test_run_v2_validation_and_report_format(self) -> None:
        report = run_v2_validation(ui=_FakeUi())
        self.assertEqual(len(report.rows), 20)
        self.assertIn(report.decision, {"cloturee", "non_cloturee"})
        markdown = format_v2_validation_report(report)
        self.assertIn("Rapport final validation V2", markdown)
        self.assertIn("17_GRILLE_V2_QUESTIONS_PME_VALIDATION.md", markdown)
        self.assertIn("Q20", markdown)

    def test_run_v2_validation_on_real_flow_with_20_questions(self) -> None:
        tmp = tempfile.mkdtemp(prefix="v2_validation_")

        def mk(idx: int, text: str, article: str, page: int | tuple[int, int]) -> DocumentChunk:
            return DocumentChunk(
                metadata=DocumentMetadata(
                    document_id="ai_act_fr_2024_1689_mvp",
                    document_title="AI Act",
                    page_number=page,
                    article_ref=article,
                    section_ref=None,
                    language="fr",
                    version_date="2024-06-13",
                    source_type="official_regulation_pdf",
                    chunk_index=idx,
                ),
                chunk_text=text,
            )

        ui = create_showcase_ui_from_chunks(
            chunks=[
                mk(1, "Le champ d'application depend de l'usage, du contexte et des exclusions.", "Article 2", 15),
                mk(2, "La qualification depend de la finalite et du niveau de risque.", "Article 3", 18),
                mk(3, "Les obligations de transparence imposent des informations claires aux utilisateurs.", "Article 13", 52),
                mk(4, "Pour les systemes high-risk, la documentation technique et les traces sont attendues.", "Article 16", (60, 61)),
                mk(5, "Le role de fournisseur, deployeur ou importateur modifie les obligations applicables.", "Article 26", 74),
            ],
            persist_directory=tmp,
            collection_name="v2_validation_collection",
            retrieval_max_distance=1.6,
        )
        report = run_v2_validation(ui=ui)
        self.assertEqual(len(report.rows), 20)
        self.assertIn(report.decision, {"cloturee", "non_cloturee"})


if __name__ == "__main__":
    unittest.main()

