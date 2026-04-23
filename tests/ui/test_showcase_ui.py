"""Tests lot 9 - parcours vitrine scenarise."""

from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path

from app.document.models import DocumentChunk, DocumentMetadata
from app.ui.app import create_showcase_ui_from_chunks, default_demo_cases


def _chunk(
    *,
    chunk_index: int,
    text: str,
    page_number: int | tuple[int, int],
    article_ref: str | None = None,
) -> DocumentChunk:
    return DocumentChunk(
        metadata=DocumentMetadata(
            document_id="ai_act_fr_2024_1689_mvp",
            document_title="AI Act",
            page_number=page_number,
            article_ref=article_ref,
            section_ref=None,
            language="fr",
            version_date="2024-06-13",
            source_type="official_regulation_pdf",
            chunk_index=chunk_index,
        ),
        chunk_text=text,
    )


class TestShowcaseUI(unittest.TestCase):
    def test_default_demo_cases_cover_expected_topics(self) -> None:
        cases = default_demo_cases()
        self.assertEqual(len(cases), 4)
        labels = " | ".join(case.title.lower() for case in cases)
        self.assertIn("transparence", labels)
        self.assertIn("sanctions", labels)
        self.assertIn("definition", labels)
        self.assertIn("hors perimetre", labels)

    def test_showcase_flow_positive_and_refusal(self) -> None:
        tmp = tempfile.mkdtemp(prefix="ui_showcase_")
        ui = create_showcase_ui_from_chunks(
            chunks=[
                _chunk(
                    chunk_index=1,
                    text="Les obligations de transparence imposent des informations claires aux utilisateurs pour les systemes IA.",
                    page_number=52,
                    article_ref="Article 13",
                ),
                _chunk(
                    chunk_index=2,
                    text="Les sanctions administratives sont precisees dans les dispositions finales du texte.",
                    page_number=261,
                    article_ref="Article 99",
                ),
            ],
            persist_directory=tmp,
            collection_name="ui_test_collection",
            retrieval_max_distance=1.5,
        )
        positive = ui.ask("Quelles obligations de transparence pour les systemes IA ?")
        self.assertFalse(positive.refusal)
        self.assertEqual(positive.business_case, "generic")
        self.assertGreaterEqual(len(positive.citations), 1)
        self.assertIn("AI Act - Article 13 - page 52", positive.citations[0])
        self.assertIn("1. Reponse simple", positive.answer_text)
        self.assertIn("6. Limites", positive.answer_text)
        self.assertIn("2. Ce que cela veut dire pour votre entreprise", positive.answer_text)
        self.assertIn("4. Ce qui reste incertain", positive.answer_text)

        refusal = ui.ask("Quel est le cadre fiscal mondial de l'IA par pays ?")
        self.assertTrue(refusal.refusal)
        self.assertEqual(refusal.business_case, "generic")
        self.assertEqual(refusal.citations, [])
        self.assertIn("Je ne peux pas conclure de maniere fiable", refusal.answer_text)

        rendered = ui.render_turn(positive)
        self.assertIn("Question:", rendered)
        self.assertIn("Retrieval:", rendered)
        self.assertIn("Citations visibles:", rendered)

    def test_no_auth_backoffice_or_saas_imports(self) -> None:
        src = Path(__file__).resolve().parents[2] / "app" / "ui" / "app.py"
        tree = ast.parse(src.read_text(encoding="utf-8"))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        joined = "\n".join(imports).lower()
        self.assertNotIn("auth", joined)
        self.assertNotIn("backoffice", joined)
        self.assertNotIn("saas", joined)


if __name__ == "__main__":
    unittest.main()

