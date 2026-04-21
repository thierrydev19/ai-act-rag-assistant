"""Tests lot 7 - generation contrainte avec citations et refus."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from app.document.models import DocumentChunk, DocumentMetadata, UserQuestion
from app.generation.service import GenerationService
from app.retrieval.service import RetrievalResult


def _chunk(
    *,
    chunk_index: int,
    text: str,
    page_number: int | tuple[int, int],
    article_ref: str | None = None,
    section_ref: str | None = None,
) -> DocumentChunk:
    return DocumentChunk(
        metadata=DocumentMetadata(
            document_id="ai_act_fr_2024_1689_mvp",
            document_title="AI Act",
            page_number=page_number,
            article_ref=article_ref,
            section_ref=section_ref,
            language="fr",
            version_date="2024-06-13",
            source_type="official_regulation_pdf",
            chunk_index=chunk_index,
        ),
        chunk_text=text,
    )


class TestGenerationService(unittest.TestCase):
    def test_generates_grounded_answer_with_citations(self) -> None:
        svc = GenerationService(max_citations=2)
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=11,
                    text="Les obligations de transparence imposent des informations claires aux utilisateurs.",
                    page_number=52,
                    article_ref="Article 13",
                ),
                _chunk(
                    chunk_index=12,
                    text="Les systemes a haut risque sont soumis a des obligations documentaires.",
                    page_number=(60, 61),
                    article_ref="Article 16",
                ),
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )

        payload = svc.generate(
            question=UserQuestion(text="Quelles obligations de transparence pour une PME ?"),
            context=context,
        )
        self.assertFalse(payload.refusal)
        self.assertIn("1. Reponse simple", payload.answer_text)
        self.assertIn("2. Ce que cela veut dire pour votre entreprise", payload.answer_text)
        self.assertIn("3. Ce qu'il faut verifier", payload.answer_text)
        self.assertIn("4. Ce qui reste incertain", payload.answer_text)
        self.assertIn("5. Sources", payload.answer_text)
        self.assertIn("6. Limites", payload.answer_text)
        self.assertEqual(len(payload.citations), 2)
        self.assertEqual(payload.intent, "transparence_information")
        self.assertIn("AI Act - Article 13 - page 52", payload.citations[0])
        self.assertIn("AI Act - Article 16 - page 60-61", payload.citations[1])

    def test_refusal_when_context_is_insufficient(self) -> None:
        svc = GenerationService()
        context = RetrievalResult(
            chunks=[],
            is_sufficient=False,
            status="insufficient",
            message="Aucun extrait pertinent trouve dans le store.",
        )
        payload = svc.generate(
            question=UserQuestion(text="Quel est le delai exact de mise en conformite ?"),
            context=context,
        )
        self.assertTrue(payload.refusal)
        self.assertEqual(payload.intent, "limites_conclusion")
        self.assertEqual(payload.citations, [])
        self.assertIn("Je ne peux pas conclure de maniere fiable", payload.answer_text)
        self.assertIn("Aucune source suffisamment pertinente", payload.answer_text)

    def test_citation_falls_back_to_page_only(self) -> None:
        svc = GenerationService(max_citations=1)
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=99,
                    text="Disposition generale applicable.",
                    page_number=222,
                    article_ref=None,
                    section_ref=None,
                )
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        payload = svc.generate(
            question=UserQuestion(text="Que dit le texte sur ce point ?"),
            context=context,
        )
        self.assertEqual(payload.intent, "limites_conclusion")
        self.assertIn("AI Act - page 222", payload.citations[0])
        self.assertNotIn("Article", payload.citations[0])

    def test_prompt_is_constrained_to_sources(self) -> None:
        svc = GenerationService(max_citations=1)
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=1,
                    text="Texte source unique.",
                    page_number=10,
                    article_ref="Article 3",
                )
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        prompt = svc.build_constrained_prompt(UserQuestion(text="Question test"), context)
        self.assertIn("uniquement avec les informations presentes", prompt)
        self.assertIn("Interdits: invention", prompt)
        self.assertIn("Texte source unique.", prompt)

    def test_no_ui_auth_multi_llm_imports(self) -> None:
        src = Path(__file__).resolve().parents[2] / "app" / "generation" / "service.py"
        tree = ast.parse(src.read_text(encoding="utf-8"))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        joined = "\n".join(imports)
        self.assertNotIn("ui", joined)
        self.assertNotIn("auth", joined)
        self.assertNotIn("openai", joined)
        self.assertNotIn("anthropic", joined)

    def test_refusal_for_out_of_scope_business_or_legal_advice(self) -> None:
        svc = GenerationService()
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=1,
                    text="Extrait quelconque.",
                    page_number=10,
                    article_ref="Article 3",
                )
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        payload = svc.generate(
            question=UserQuestion(text="Quel est le meilleur choix de fournisseur pour ma strategie commerciale ?"),
            context=context,
        )
        self.assertTrue(payload.refusal)
        self.assertEqual(payload.intent, "limites_conclusion")
        self.assertEqual(payload.citations, [])
        self.assertIn("hors perimetre documentaire", payload.answer_text)

    def test_intent_classification_for_obligations(self) -> None:
        svc = GenerationService()
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=1,
                    text="Les obligations des fournisseurs sont detaillees.",
                    page_number=12,
                    article_ref="Article 16",
                )
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        payload = svc.generate(
            question=UserQuestion(text="Quelles obligations pour notre entreprise ?"),
            context=context,
        )
        self.assertEqual(payload.intent, "obligations_entreprise")

    def test_intent_classification_for_qualification_and_documentation(self) -> None:
        svc = GenerationService()
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=2,
                    text="La documentation des systemes IA doit etre maintenue et verifiable.",
                    page_number=20,
                    article_ref="Article 11",
                )
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        payload_qualification = svc.generate(
            question=UserQuestion(text="Comment qualifier un systeme IA ?"),
            context=context,
        )
        payload_documentation = svc.generate(
            question=UserQuestion(text="Quelles preuves de documentation faut-il conserver ?"),
            context=context,
        )
        self.assertEqual(payload_qualification.intent, "qualification_systeme")
        self.assertEqual(payload_documentation.intent, "documentation_preuves")


if __name__ == "__main__":
    unittest.main()

