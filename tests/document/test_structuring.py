"""Tests de structuration documentaire — extraction d'article par page."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from pypdf import PdfReader

from app.document.article_extraction import (
    extract_article_ref_from_page_text,
    extract_section_ref_from_page_text,
)
from app.document.structuring import structure_ingested_pdf
from app.ingestion.service import IngestionService, mvp_ai_act_french_pdf_path


class TestArticleExtraction(unittest.TestCase):
    """Le bloc dédié, isolé, qui teste la regex sans charger le PDF."""

    def test_line_start_article_single(self) -> None:
        text = "Article 5\nLes fournisseurs..."
        self.assertEqual(extract_article_ref_from_page_text(text), "Article 5")

    def test_rejects_inline_l_article(self) -> None:
        text = "Conformément à l'article 6, paragraphe 2, le système..."
        self.assertIsNone(extract_article_ref_from_page_text(text))

    def test_rejects_multiple_distinct_articles(self) -> None:
        text = "Article 5\n... contenu ...\nArticle 7\n... autre contenu ..."
        self.assertIsNone(extract_article_ref_from_page_text(text))

    def test_rejects_toc_dot_leaders(self) -> None:
        text = "Article 6 .................................. 17"
        self.assertIsNone(extract_article_ref_from_page_text(text))

    def test_section_ref_always_none_in_lot3(self) -> None:
        self.assertIsNone(extract_section_ref_from_page_text("anything"))


class TestStructureIngestedPdf(unittest.TestCase):
    """Validation structuration sur un PDF synthétique et sur le PDF officiel."""

    def test_structure_from_synthetic_ingested(self) -> None:
        from app.document.models import IngestedPdfDocument, RawDocumentPage

        synthetic = IngestedPdfDocument(
            source_path="/tmp/x.pdf",
            pages=(
                RawDocumentPage(page_number=1, text="Article 3\nDéfinitions..."),
                RawDocumentPage(page_number=2, text="suite article 3..."),
            ),
        )
        structured = structure_ingested_pdf(synthetic)
        self.assertEqual(len(structured.pages), 2)
        u1 = structured.pages[0]
        self.assertEqual(u1.trace.article_ref, "Article 3")
        self.assertEqual(u1.trace.page_number, 1)
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
        """Garde-fous structurels sur le PDF officiel (UE 2024/1689 FR, 144 pages JO).

        On évite les assertions sur des numéros de page absolus, qui dépendent du
        format de mise en page. On valide plutôt des invariants robustes :
        couverture, présence d'articles structurants typiques, absence de
        section_ref, et fidélité du texte.

        Note sur la couverture : le détecteur est volontairement conservateur
        (rejet des pages qui présentent plusieurs numéros distincts en tête de
        ligne, fréquent sur des articles longs avec références internes). Une
        couverture de ~25-35 articles uniques sur 144 pages JO est attendue.
        Une amélioration future (propagation d'article_ref entre pages) est un
        chantier séparé.
        """
        path = mvp_ai_act_french_pdf_path()
        if not path.is_file():
            self.skipTest(f"PDF MVP absent: {path}")

        ingested = IngestionService().ingest_pdf(path)
        structured = structure_ingested_pdf(ingested)

        reader = PdfReader(str(path))
        self.assertEqual(len(structured.pages), len(reader.pages))

        # Invariant 1 : chaque page structurée correspond exactement à la page brute.
        for raw, unit in zip(ingested.pages, structured.pages, strict=True):
            self.assertEqual(unit.trace.page_number, raw.page_number)
            self.assertEqual(unit.text, raw.text)

        # Invariant 2 : section_ref est universellement None dans ce lot.
        for unit in structured.pages:
            self.assertIsNone(unit.trace.section_ref)

        # Invariant 3 : couverture minimale d'articles identifiés.
        identified = [
            (u.trace.page_number, u.trace.article_ref)
            for u in structured.pages
            if u.trace.article_ref
        ]
        article_refs = {ref for _, ref in identified}
        self.assertGreater(
            len(article_refs),
            20,
            f"Sur 144 pages du règlement officiel, on attend au moins 20 articles "
            f"uniques identifiés (constaté: {len(article_refs)}).",
        )

        # Invariant 4 : présence d'articles structurants des premières dispositions.
        # On exige au moins 5 articles parmi les 30 premiers (qualification, risques,
        # définitions, pratiques interdites, etc.). La liste exacte d'articles
        # détectés varie : ce qui compte c'est qu'on capture le début du règlement.
        early_articles = [
            ref for ref in article_refs
            if ref.startswith("Article ") and ref.split()[1].isdigit()
            and int(ref.split()[1]) <= 30
        ]
        self.assertGreaterEqual(
            len(early_articles),
            5,
            f"Au moins 5 articles dans la plage 1-30 doivent être identifiés "
            f"(constaté: {sorted(early_articles)}).",
        )

        # Invariant 5 : monotonie globale des numéros d'articles.
        # Les références doivent globalement progresser au fil des pages
        # (tolérance: <3 régressions sur l'ensemble du document).
        def article_number(ref: str) -> int:
            token = ref.split()[1]
            return int(token) if token.isdigit() else 0

        previous = 0
        regressions = 0
        for _, ref in identified:
            current = article_number(ref)
            if current and current < previous:
                regressions += 1
            if current:
                previous = max(previous, current)
        self.assertLess(
            regressions,
            3,
            f"Les références d'articles doivent globalement progresser au fil "
            f"des pages (constaté: {regressions} régressions).",
        )


if __name__ == "__main__":
    unittest.main()
