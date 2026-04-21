"""Lot 8 - test e2e minimal sur scenario positif et refus."""

from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path

from app.document.models import DocumentChunk, DocumentMetadata, UserQuestion
from app.main import run_e2e_demo


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


class TestE2EFlow(unittest.TestCase):
    def test_positive_and_refusal_scenarios(self) -> None:
        tmp = tempfile.mkdtemp(prefix="e2e_demo_")
        demo_chunks = [
            _chunk(
                chunk_index=1,
                text="Les obligations de transparence imposent des informations claires aux utilisateurs pour les systemes IA.",
                page_number=52,
                article_ref="Article 13",
            ),
            _chunk(
                chunk_index=2,
                text="Les systemes a haut risque necessitent une documentation technique detaillee.",
                page_number=(60, 61),
                article_ref="Article 16",
            ),
        ]
        questions = [
            UserQuestion(text="Quelles obligations de transparence pour une PME ?"),
            UserQuestion(text="Quel est le regime fiscal de l'IA dans tous les pays ?"),
        ]

        results = run_e2e_demo(
            questions,
            chunks=demo_chunks,
            persist_directory=tmp,
            collection_name="e2e_test_collection",
            retrieval_top_k=2,
            retrieval_max_distance=1.5,
        )

        self.assertEqual(len(results), 2)

        positive = results[0]
        self.assertTrue(positive.retrieval.is_sufficient)
        self.assertFalse(positive.answer.refusal)
        self.assertGreaterEqual(len(positive.answer.citations), 1)
        self.assertIn("AI Act - Article 13 - page 52", positive.answer.citations[0])
        self.assertIn("5. Sources", positive.answer.answer_text)

        negative = results[1]
        self.assertTrue(negative.answer.refusal)
        self.assertIn("Je ne peux pas conclure de maniere fiable", negative.answer.answer_text)
        self.assertEqual(negative.answer.citations, [])

    def test_no_ui_saas_auth_addition_in_main(self) -> None:
        src = Path(__file__).resolve().parents[2] / "app" / "main.py"
        tree = ast.parse(src.read_text(encoding="utf-8"))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        joined = "\n".join(imports)
        self.assertNotIn("auth", joined)
        self.assertNotIn("saaS", joined.lower())


if __name__ == "__main__":
    unittest.main()

