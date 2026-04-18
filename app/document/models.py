"""Structures de données de base pour le socle MVP.

Ce module définit uniquement les contrats de données.
La logique documentaire réelle sera implémentée dans les lots suivants.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DocumentMetadata:
    """Métadonnées minimales obligatoires pour un chunk citable."""

    document_id: str
    document_title: str
    page_number: int
    article_ref: str
    section_ref: Optional[str]
    language: str
    version_date: str
    source_type: str
    chunk_index: int


@dataclass(frozen=True)
class DocumentChunk:
    """Unité documentaire prête pour les étapes embeddings/retrieval."""

    metadata: DocumentMetadata
    chunk_text: str


@dataclass(frozen=True)
class RawDocumentPage:
    """Texte extrait pour une page physique du PDF (lot 2, sans chunking)."""

    page_number: int
    text: str


@dataclass(frozen=True)
class IngestedPdfDocument:
    """Base documentaire brute : une entrée par page PDF, ordre conservé."""

    source_path: str
    pages: tuple[RawDocumentPage, ...]


@dataclass(frozen=True)
class DocumentPageTrace:
    """Métadonnées minimales par page physique (lot 3), sans chunk_index."""

    document_id: str
    document_title: str
    page_number: int
    article_ref: Optional[str]
    section_ref: Optional[str]
    language: str
    version_date: str
    source_type: str


@dataclass(frozen=True)
class DocumentPageUnit:
    """Unité documentaire par page : traçabilité + texte brut pour le lot 4."""

    trace: DocumentPageTrace
    text: str


@dataclass(frozen=True)
class StructuredPdfDocument:
    """Document structuré après lot 3 (une unité par page PDF)."""

    source_path: str
    pages: tuple[DocumentPageUnit, ...]


@dataclass(frozen=True)
class UserQuestion:
    """Question utilisateur reçue par le pipeline applicatif."""

    text: str
    language: str = "fr"

