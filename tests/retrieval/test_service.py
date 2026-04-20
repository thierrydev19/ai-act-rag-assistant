"""Tests lot 6 - retrieval semantique."""

from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path

from app.document.models import DocumentChunk, DocumentMetadata, UserQuestion
from app.embeddings.store import VectorStore
from app.retrieval.service import RetrievalService


def _mk_chunk(
    *,
    chunk_index: int,
    text: str,
    article_ref: str | None,
    page_number: int | tuple[int, int],
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


class TestRetrievalService(unittest.TestCase):
    def test_retrieve_relevant_chunks_with_metadata(self) -> None:
        tmp = tempfile.mkdtemp(prefix="retrieval_test_")
        store = VectorStore(persist_directory=tmp, collection_name="retrieval_demo")
        store.index(
            [
                _mk_chunk(
                    chunk_index=1,
                    text="Les obligations de transparence des systemes d'IA a haut risque sont detaillees.",
                    article_ref="Article 13",
                    page_number=12,
                ),
                _mk_chunk(
                    chunk_index=2,
                    text="Les definitions du reglement europeen sur l'intelligence artificielle.",
                    article_ref="Article 3",
                    page_number=(8, 9),
                ),
            ]
        )
        svc = RetrievalService(
            vector_store=store,
            top_k=2,
            max_acceptable_distance=1.35,
            relaxed_max_distance=1.6,
            min_lexical_overlap=0.05,
            min_combined_score=0.05,
        )

        result = svc.retrieve(UserQuestion(text="Quelles obligations de transparence sont prevues ?"))
        self.assertTrue(result.is_sufficient)
        self.assertEqual(result.status, "sufficient")
        self.assertGreaterEqual(len(result.chunks), 1)
        top = result.chunks[0]
        self.assertEqual(top.metadata.document_id, "ai_act_fr_2024_1689_mvp")
        self.assertEqual(top.metadata.language, "fr")
        self.assertIsNotNone(top.metadata.chunk_index)
        self.assertTrue(top.chunk_text.strip())

    def test_empty_question_is_explicitly_insufficient(self) -> None:
        tmp = tempfile.mkdtemp(prefix="retrieval_empty_")
        store = VectorStore(persist_directory=tmp, collection_name="retrieval_empty")
        svc = RetrievalService(vector_store=store)
        result = svc.retrieve(UserQuestion(text=""))
        self.assertFalse(result.is_sufficient)
        self.assertEqual(result.status, "insufficient")
        self.assertEqual(result.chunks, [])

    def test_multiple_realistic_questions(self) -> None:
        tmp = tempfile.mkdtemp(prefix="retrieval_questions_")
        store = VectorStore(persist_directory=tmp, collection_name="retrieval_questions")
        store.index(
            [
                _mk_chunk(
                    chunk_index=10,
                    text="Les systemes d'IA a haut risque doivent respecter des exigences strictes de gestion des risques.",
                    article_ref="Article 9",
                    page_number=44,
                ),
                _mk_chunk(
                    chunk_index=11,
                    text="Les obligations de transparence imposent des informations claires aux utilisateurs.",
                    article_ref="Article 13",
                    page_number=52,
                ),
                _mk_chunk(
                    chunk_index=12,
                    text="Le regime des sanctions administratives est detaille dans les dispositions finales.",
                    article_ref="Article 99",
                    page_number=(260, 261),
                ),
            ]
        )
        svc = RetrievalService(
            vector_store=store,
            top_k=2,
            max_acceptable_distance=1.35,
            relaxed_max_distance=1.6,
            min_lexical_overlap=0.05,
            min_combined_score=0.05,
        )
        questions = [
            "Quelles sont les obligations de transparence ?",
            "Comment sont encadres les systemes a haut risque ?",
            "Quelles sanctions sont prevues en cas de non-conformite ?",
        ]
        for q in questions:
            with self.subTest(question=q):
                result = svc.retrieve(UserQuestion(text=q))
                self.assertGreaterEqual(len(result.chunks), 1)
                first = result.chunks[0]
                self.assertIsNotNone(first.metadata.document_id)
                self.assertIsNotNone(first.metadata.chunk_index)
                self.assertIsNotNone(first.metadata.page_number)
                self.assertTrue(first.chunk_text.strip())

    def test_hybrid_ranking_prioritizes_lexically_related_chunk(self) -> None:
        tmp = tempfile.mkdtemp(prefix="retrieval_hybrid_")
        store = VectorStore(persist_directory=tmp, collection_name="retrieval_hybrid")
        store.index(
            [
                _mk_chunk(
                    chunk_index=30,
                    text="Regles generales sans mention de transparence explicite.",
                    article_ref="Article 1",
                    page_number=10,
                ),
                _mk_chunk(
                    chunk_index=31,
                    text="Les obligations de transparence imposent des informations claires aux utilisateurs.",
                    article_ref="Article 13",
                    page_number=52,
                ),
            ]
        )
        svc = RetrievalService(
            vector_store=store,
            top_k=1,
            max_acceptable_distance=1.35,
            relaxed_max_distance=1.6,
            min_lexical_overlap=0.05,
            min_combined_score=0.05,
        )
        result = svc.retrieve(UserQuestion(text="Obligations de transparence pour utilisateurs"))
        self.assertTrue(result.chunks)
        self.assertEqual(result.chunks[0].metadata.article_ref, "Article 13")

    def test_no_generation_or_ui_or_auth_imports(self) -> None:
        src = Path(__file__).resolve().parents[2] / "app" / "retrieval" / "service.py"
        tree = ast.parse(src.read_text(encoding="utf-8"))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        joined = "\n".join(imports)
        self.assertNotIn("generation", joined)
        self.assertNotIn("ui", joined)
        self.assertNotIn("auth", joined)


if __name__ == "__main__":
    unittest.main()

