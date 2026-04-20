"""Tests lot 4 — chunking juridique traçable et citabilité."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from app.chunking.service import ChunkingService
from app.document.models import DocumentPageTrace, DocumentPageUnit, StructuredPdfDocument


def _mk_page(
    page_number: int,
    text: str,
    article_ref: str | None,
    section_ref: str | None = None,
) -> DocumentPageUnit:
    trace = DocumentPageTrace(
        document_id="doc-1",
        document_title="AI Act test",
        page_number=page_number,
        article_ref=article_ref,
        section_ref=section_ref,
        language="fr",
        version_date="2024-06-13",
        source_type="official_regulation_pdf",
    )
    return DocumentPageUnit(trace=trace, text=text)


class TestChunkingService(unittest.TestCase):
    def test_short_article_stays_single_chunk(self) -> None:
        paragraph = " ".join(f"mot{i}" for i in range(1, 121))
        page = _mk_page(10, f"Article 12\n\n{paragraph}", "Article 12")
        structured = StructuredPdfDocument(source_path="/tmp/a.pdf", pages=(page,))

        svc = ChunkingService(min_words=80, max_words=200, overlap_ratio=0.12)
        chunks = svc.split(structured)

        self.assertEqual(len(chunks), 1)
        chunk = chunks[0]
        self.assertEqual(chunk.metadata.chunk_index, 1)
        self.assertEqual(chunk.metadata.page_number, 10)
        self.assertEqual(chunk.metadata.article_ref, "Article 12")
        self.assertIn("Article 12", chunk.chunk_text)

    def test_long_article_splits_with_overlap_and_page_range(self) -> None:
        p1 = " ".join(f"a{i}" for i in range(1, 171))
        p2 = " ".join(f"b{i}" for i in range(1, 171))
        p3 = " ".join(f"c{i}" for i in range(1, 171))
        page_1 = _mk_page(20, f"Article 15\n\n{p1}\n\n{p2}", "Article 15")
        page_2 = _mk_page(21, p3, "Article 15")
        structured = StructuredPdfDocument(source_path="/tmp/a.pdf", pages=(page_1, page_2))

        svc = ChunkingService(min_words=180, max_words=320, overlap_ratio=0.12)
        chunks = svc.split(structured)

        self.assertGreaterEqual(len(chunks), 2)
        self.assertEqual(
            [c.metadata.chunk_index for c in chunks],
            list(range(1, len(chunks) + 1)),
        )
        self.assertTrue(all(c.metadata.article_ref == "Article 15" for c in chunks))
        self.assertEqual(chunks[-1].metadata.page_number, (20, 21))

        words0 = chunks[0].chunk_text.split()
        words1 = chunks[1].chunk_text.split()
        overlap_target = int(320 * 0.12)
        overlap_tail = words0[-overlap_target:]
        self.assertEqual(words1[: len(overlap_tail)], overlap_tail)

    def test_missing_article_ref_is_preserved_as_none(self) -> None:
        text = " ".join(f"x{i}" for i in range(1, 141))
        structured = StructuredPdfDocument(
            source_path="/tmp/a.pdf",
            pages=(_mk_page(2, text, None), _mk_page(3, text, None)),
        )
        svc = ChunkingService(min_words=100, max_words=220, overlap_ratio=0.1)
        chunks = svc.split(structured)
        self.assertGreaterEqual(len(chunks), 1)
        for chunk in chunks:
            self.assertIsNone(chunk.metadata.article_ref)

    def test_chunking_module_does_not_import_embeddings_retrieval_generation(self) -> None:
        src = Path(__file__).resolve().parents[2] / "app" / "chunking" / "service.py"
        tree = ast.parse(src.read_text(encoding="utf-8"))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        joined = "\n".join(imports)
        self.assertNotIn("embeddings", joined)
        self.assertNotIn("retrieval", joined)
        self.assertNotIn("generation", joined)


if __name__ == "__main__":
    unittest.main()

