"""Structuration documentaire : sortie lot 2 + métadonnées minimales (lot 3)."""

from __future__ import annotations

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
from app.document.models import (
    DocumentPageTrace,
    DocumentPageUnit,
    IngestedPdfDocument,
    StructuredPdfDocument,
)
from app.logging.logger import get_logger

logger = get_logger(__name__)


def structure_ingested_pdf(ingested: IngestedPdfDocument) -> StructuredPdfDocument:
    """Enrichit chaque page brute avec les métadonnées de traçabilité MVP."""
    units: list[DocumentPageUnit] = []
    for raw in ingested.pages:
        article_ref = extract_article_ref_from_page_text(raw.text)
        section_ref = extract_section_ref_from_page_text(raw.text)
        trace = DocumentPageTrace(
            document_id=MVP_DOCUMENT_ID,
            document_title=MVP_DOCUMENT_TITLE,
            page_number=raw.page_number,
            article_ref=article_ref,
            section_ref=section_ref,
            language=MVP_LANGUAGE,
            version_date=MVP_VERSION_DATE,
            source_type=MVP_SOURCE_TYPE,
        )
        units.append(DocumentPageUnit(trace=trace, text=raw.text))
    logger.info(
        "Structuration documentaire | source=%s | pages=%s",
        ingested.source_path,
        len(units),
    )
    return StructuredPdfDocument(
        source_path=ingested.source_path,
        pages=tuple(units),
    )
