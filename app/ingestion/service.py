"""Service d'ingestion documentaire — lot 2 : PDF officiel, texte et pages."""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from app.document.models import IngestedPdfDocument, RawDocumentPage
from app.logging.logger import get_logger

logger = get_logger(__name__)


def mvp_ai_act_french_pdf_path(repo_root: Path | None = None) -> Path:
    """Chemin du PDF unique MVP (AI Act, français), relatif à la racine du dépôt."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "docs" / "ToC-AI-Act-French.pdf"


class IngestionService:
    """Charge un PDF, extrait le texte page par page (index physique 1..n)."""

    def ingest_pdf(self, source_path: str | Path) -> IngestedPdfDocument:
        path = Path(source_path).expanduser().resolve()
        if not path.is_file():
            msg = f"Document introuvable: {path}"
            logger.error(msg)
            raise FileNotFoundError(msg)
        if path.suffix.lower() != ".pdf":
            msg = f"Format non pris en charge (PDF attendu): {path}"
            logger.error(msg)
            raise ValueError(msg)

        logger.info("Ingestion PDF | path=%s", path)
        reader = PdfReader(str(path))
        total = len(reader.pages)
        logger.info("Ingestion PDF | pages_pdf=%s", total)

        raw_pages: list[RawDocumentPage] = []
        empty_pages: list[int] = []

        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text is None:
                text = ""
            stripped = text.strip()
            if not stripped:
                empty_pages.append(index)
                logger.warning(
                    "Page sans texte extractible (pas d'OCR dans ce lot) | page=%s",
                    index,
                )
            raw_pages.append(RawDocumentPage(page_number=index, text=text))

        if empty_pages:
            logger.warning(
                "Ingestion terminée avec pages vides | count=%s | exemple=%s",
                len(empty_pages),
                empty_pages[:10],
            )

        joined = "\n".join(p.text.strip() for p in raw_pages)
        if not joined.strip():
            msg = "Aucun texte extractible sur l'ensemble du document (extraction réputée échouée)."
            logger.error(msg)
            raise ValueError(msg)

        logger.info(
            "Ingestion PDF | pages_avec_texte=%s | caracteres_total=%s",
            total - len(empty_pages),
            len(joined),
        )

        resolved = str(path)
        return IngestedPdfDocument(
            source_path=resolved,
            pages=tuple(raw_pages),
        )
