"""Lot 3 — métadonnées minimales et structuration sans chunking."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from pypdf import PdfReader

from app.document.article_extraction import (
    extract_article_ref_from_page_text,
    extract_section_ref_from_page_text,
)
from app.document.constants import (
    MVP_DOCUMENT_ID,
    MVP_DOCUMENT_TITLE,
    MVP_LANGUAGE,
    MVP_SOURCE_TYPE,
    MVP_VERSION_DATE,
)
from app.document.models import IngestedPdfDocument, RawDocumentPage
from app.document.structuring import structure_ingested_pdf
from app.ingestion.service import IngestionService, mvp_ai_act_french_pdf_path


class TestArticleExtraction(unittest.TestCase):
    """Heuristique article : pas de faux positifs évidents, pas d'invention."""

    def test_line_start_article_single(self) -> None:
        text = "Entête\nArticle 7 - Titre\nCorps"
        self.assertEqual(extract_article_ref_from_page_text(text), "Article 7")

    def test_rejects_inline_l_article(self) -> None:
        text = "au sens de l'article 2, point 4), de la directive"
        self.assertIsNone(extract_article_ref_from_page_text(text))

    def test_rejects_toc_dot_leaders(self) -> None:
        text = "ARTICLE 73 - TITRE ........................................................"
        self.assertIsNone(extract_article_ref_from_page_text(text))

    def test_rejects_multiple_distinct_articles(self) -> None:
        text = "Article 35 - A 1. x\nArticle 36 - B 2. y"
        self.assertIsNone(extract_article_ref_from_page_text(text))

    def test_section_ref_always_none_in_lot3(self) -> None:
        self.assertIsNone(extract_section_ref_from_page_text("Chapitre I\nArticle 1"))


class TestStructureIngestedPdf(unittest.TestCase):
    """Champs minimaux, conservation page et texte, pas de chunking."""

    def test_structure_from_synthetic_ingested(self) -> None:
        ingested = IngestedPdfDocument(
            source_path="/tmp/x.pdf",
            pages=(
                RawDocumentPage(page_number=1, text="Page un"),
                RawDocumentPage(
                    page_number=2,
                    text="Suite\nArticle 3 - Champ d'application\nParagraphe",
                ),
            ),
        )
        structured = structure_ingested_pdf(ingested)
        self.assertEqual(structured.source_path, "/tmp/x.pdf")
        self.assertEqual(len(structured.pages), 2)
        u0 = structured.pages[0]
        self.assertEqual(u0.trace.page_number, 1)
        self.assertEqual(u0.trace.document_id, MVP_DOCUMENT_ID)
        self.assertEqual(u0.trace.document_title, MVP_DOCUMENT_TITLE)
        self.assertEqual(u0.trace.language, MVP_LANGUAGE)
        self.assertEqual(u0.trace.version_date, MVP_VERSION_DATE)
        self.assertEqual(u0.trace.source_type, MVP_SOURCE_TYPE)
        self.assertIsNone(u0.trace.article_ref)
        self.assertIsNone(u0.trace.section_ref)
        self.assertEqual(u0.text, "Page un")
        u1 = structured.pages[1]
        self.assertEqual(u1.trace.page_number, 2)
        self.assertEqual(u1.trace.article_ref, "Article 3")
        self.assertIsNone(u1.trace.section_ref)
        self.assertIn("Article 3", u1.text)

    def test_no_chunking_in_document_modules(self) -> None:
        root = Path(__file__).resolve().parents[2] / "app" / "document"
        for name in ("structuring.py", "article_extraction.py"):
            src = root / name
            tree = ast.parse(src.read_text(encoding="utf-8"))
            mods: list[str] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    mods.append(node.module)
                elif isinstance(node, ast.Import):
                    for a in node.names:
                        mods.append(a.name)
            joined = "\n".join(mods)
            self.assertNotIn("chunking", joined)
            self.assertNotIn("embeddings", joined)
            self.assertNotIn("retrieval", joined)

    def test_official_pdf_sample_pages_when_present(self) -> None:
        path = mvp_ai_act_french_pdf_path()
        if not path.is_file():
            self.skipTest(f"PDF MVP absent: {path}")

        ingested = IngestionService().ingest_pdf(path)
        structured = structure_ingested_pdf(ingested)

        reader = PdfReader(str(path))
        self.assertEqual(len(structured.pages), len(reader.pages))

        for raw, unit in zip(ingested.pages, structured.pages, strict=True):
            self.assertEqual(unit.trace.page_number, raw.page_number)
            self.assertEqual(unit.text, raw.text)

        p200 = structured.pages[199]
        self.assertEqual(p200.trace.article_ref, "Article 7")
        p210 = structured.pages[209]
        self.assertEqual(p210.trace.article_ref, "Article 10")

        p264 = structured.pages[263]
        self.assertIsNone(
            p264.trace.article_ref,
            "Deux articles distincts en tête de ligne → aucune référence décidée",
        )

        p40 = structured.pages[39]
        self.assertIsNone(
            p40.trace.article_ref,
            "Référence « l'article » dans le corps ne doit pas produire de titre",
        )

        for unit in structured.pages:
            self.assertIsNone(unit.trace.section_ref)


if __name__ == "__main__":
    unittest.main()
