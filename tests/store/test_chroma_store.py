"""Tests Chroma lot 5 : indexation, persistance, relecture."""

from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path

from app.document.models import DocumentChunk, DocumentMetadata
from app.embeddings.store import VectorStore


def _chunk(
    *,
    chunk_index: int,
    page_number: int | tuple[int, int],
    article_ref: str | None,
    section_ref: str | None,
    text: str,
) -> DocumentChunk:
    metadata = DocumentMetadata(
        document_id="doc-ai-act",
        document_title="AI Act",
        page_number=page_number,
        article_ref=article_ref,
        section_ref=section_ref,
        language="fr",
        version_date="2024-06-13",
        source_type="official_regulation_pdf",
        chunk_index=chunk_index,
    )
    return DocumentChunk(metadata=metadata, chunk_text=text)


class TestChromaVectorStore(unittest.TestCase):
    def test_indexed_chunk_can_be_reloaded_with_metadata(self) -> None:
        tmp = tempfile.mkdtemp(prefix="chroma_test_idx_")
        store = VectorStore(persist_directory=tmp, collection_name="test_idx")
        chunk = _chunk(
            chunk_index=1,
            page_number=(12, 13),
            article_ref=None,
            section_ref=None,
            text="Texte juridique article long.",
        )
        store.index([chunk])

        loaded = store.get_by_chunk_id("doc-ai-act:1")
        self.assertEqual(loaded.chunk_text, chunk.chunk_text)
        self.assertEqual(loaded.metadata.document_id, "doc-ai-act")
        self.assertEqual(loaded.metadata.page_number, (12, 13))
        self.assertIsNone(loaded.metadata.article_ref)
        self.assertIsNone(loaded.metadata.section_ref)
        self.assertEqual(loaded.metadata.chunk_index, 1)

    def test_store_persistence_across_instances(self) -> None:
        tmp = tempfile.mkdtemp(prefix="chroma_test_persist_")
        s1 = VectorStore(persist_directory=tmp, collection_name="test_persist")
        s1.index(
            [
                _chunk(
                    chunk_index=8,
                    page_number=45,
                    article_ref="Article 7",
                    section_ref=None,
                    text="Obligations de transparence.",
                )
            ]
        )
        s2 = VectorStore(persist_directory=tmp, collection_name="test_persist")
        loaded = s2.get_by_chunk_id("doc-ai-act:8")
        self.assertEqual(loaded.metadata.page_number, 45)
        self.assertEqual(loaded.metadata.article_ref, "Article 7")

    def test_embeddings_exist_for_indexed_chunks(self) -> None:
        tmp = tempfile.mkdtemp(prefix="chroma_test_embed_")
        store = VectorStore(persist_directory=tmp, collection_name="test_embed")
        store.index(
            [
                _chunk(
                    chunk_index=2,
                    page_number=9,
                    article_ref="Article 3",
                    section_ref=None,
                    text="Definition des systemes IA.",
                )
            ]
        )
        emb = store.get_embedding_by_chunk_id("doc-ai-act:2")
        self.assertGreater(len(emb), 0)
        self.assertTrue(any(abs(x) > 0 for x in emb))

    def test_no_retrieval_or_generation_in_store_module(self) -> None:
        src = Path(__file__).resolve().parents[2] / "app" / "embeddings" / "store.py"
        tree = ast.parse(src.read_text(encoding="utf-8"))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        joined = "\n".join(imports)
        self.assertNotIn("retrieval", joined)
        self.assertNotIn("generation", joined)
        self.assertNotIn("ui", joined)


if __name__ == "__main__":
    unittest.main()

