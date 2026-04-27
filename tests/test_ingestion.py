"""Tests d'ingestion lot 2 — PDF officiel AI Act (français)."""

from __future__ import annotations

import unittest
from pathlib import Path

from pypdf import PdfReader

from app.ingestion.service import IngestionService, mvp_ai_act_french_pdf_path


class TestIngestionService(unittest.TestCase):
    """Validation chargement, texte non vide, repérage des pages."""

    def test_ingest_raises_file_not_found(self) -> None:
        svc = IngestionService()
        with self.assertRaises(FileNotFoundError):
            svc.ingest_pdf(Path(__file__).resolve().parent / "no_such_file.pdf")

    def test_ingest_raises_non_pdf(self) -> None:
        svc = IngestionService()
        fake = Path(__file__).resolve()
        with self.assertRaises(ValueError) as ctx:
            svc.ingest_pdf(fake)
        self.assertIn("PDF", str(ctx.exception))

    def test_official_pdf_when_present(self) -> None:
        path = mvp_ai_act_french_pdf_path()
        if not path.is_file():
            self.skipTest(f"PDF MVP absent (ajouter le fichier): {path}")

        reader = PdfReader(str(path))
        expected_page_count = len(reader.pages)

        svc = IngestionService()
        doc = svc.ingest_pdf(path)

        self.assertEqual(doc.source_path, str(path.resolve()))
        self.assertEqual(len(doc.pages), expected_page_count)

        numbers = [p.page_number for p in doc.pages]
        self.assertEqual(numbers, list(range(1, expected_page_count + 1)))

        total_chars = sum(len(p.text.strip()) for p in doc.pages)
        self.assertGreater(total_chars, 10_000, "Le texte extrait ne doit pas être vide")

        # Échantillon : page 1 = couverture du JO avec la référence officielle du règlement.
        # On accepte les variantes d'extraction pypdf (espaces parasites éventuels après majuscules).
        p1_normalized = doc.pages[0].text.replace(" ", "")
        self.assertIn(
            "2024/1689",
            p1_normalized,
            "Page 1 : référence du règlement attendue (UE 2024/1689)",
        )
        self.assertIn(
            "REGLEMENT".lower(),
            doc.pages[0].text.lower().replace(" ", "").replace("è", "e"),
            "Page 1 : entête 'RÈGLEMENT' attendue",
        )

        # Échantillon : page 2 (corps, texte long)
        p2 = doc.pages[1].text
        self.assertGreater(len(p2.strip()), 500, "Page 2 : texte substantiel attendu")

    def test_no_chunking_module_in_ingestion(self) -> None:
        """Garde-fou périmètre lot 2 : pas d'import chunking depuis l'ingestion."""
        import ast
        from pathlib import Path

        src = Path(__file__).resolve().parents[1] / "app" / "ingestion" / "service.py"
        tree = ast.parse(src.read_text(encoding="utf-8"))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        joined = "\n".join(imports)
        self.assertNotIn("chunking", joined)


if __name__ == "__main__":
    unittest.main()