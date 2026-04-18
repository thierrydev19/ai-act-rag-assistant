"""Modèles documentaires et métadonnées du MVP."""

from app.document.constants import (
    MVP_DOCUMENT_ID,
    MVP_DOCUMENT_TITLE,
    MVP_LANGUAGE,
    MVP_SOURCE_TYPE,
    MVP_VERSION_DATE,
)
from app.document.models import (
    DocumentChunk,
    DocumentMetadata,
    DocumentPageTrace,
    DocumentPageUnit,
    IngestedPdfDocument,
    RawDocumentPage,
    StructuredPdfDocument,
    UserQuestion,
)
from app.document.structuring import structure_ingested_pdf

__all__ = [
    "DocumentChunk",
    "DocumentMetadata",
    "DocumentPageTrace",
    "DocumentPageUnit",
    "IngestedPdfDocument",
    "MVP_DOCUMENT_ID",
    "MVP_DOCUMENT_TITLE",
    "MVP_LANGUAGE",
    "MVP_SOURCE_TYPE",
    "MVP_VERSION_DATE",
    "RawDocumentPage",
    "StructuredPdfDocument",
    "UserQuestion",
    "structure_ingested_pdf",
]
