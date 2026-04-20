"""Service de chunking documentaire (lot 4).

Stratégie:
- priorité à la cohérence juridique et à la citation fiable;
- un article reste entier si sa taille reste raisonnable;
- découpage interne uniquement si un article est trop long;
- overlap léger (12% par défaut) entre chunks successifs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.document.models import DocumentChunk, DocumentMetadata, StructuredPdfDocument
from app.logging.logger import get_logger

logger = get_logger(__name__)

_WORD_RE = re.compile(r"\S+")


@dataclass(frozen=True)
class _TextBlock:
    """Bloc textuel élémentaire portant sa page d'origine."""

    text: str
    page_number: int


class ChunkingService:
    """Découpe un document structuré en chunks juridiques citables."""

    def __init__(
        self,
        *,
        min_words: int = 400,
        max_words: int = 800,
        overlap_ratio: float = 0.12,
    ) -> None:
        if min_words <= 0:
            raise ValueError("min_words doit être strictement positif.")
        if max_words < min_words:
            raise ValueError("max_words doit être >= min_words.")
        if overlap_ratio < 0:
            raise ValueError("overlap_ratio doit être positif.")
        self._min_words = min_words
        self._max_words = max_words
        self._overlap_ratio = overlap_ratio
        self._max_body_words = max(
            1,
            max_words - max(1, int(max_words * overlap_ratio)),
        )

    def split(self, structured: StructuredPdfDocument) -> list[DocumentChunk]:
        """Produit des chunks traçables à partir des unités documentaires lot 3."""
        grouped_pages = self._group_pages_by_article(structured)
        chunks: list[DocumentChunk] = []
        next_chunk_index = 1

        for pages in grouped_pages:
            blocks = self._build_text_blocks(pages)
            chunks_for_group = self._split_blocks(blocks)
            article_ref = pages[0].trace.article_ref
            section_ref = pages[0].trace.section_ref
            for group_chunk in chunks_for_group:
                meta = pages[0].trace
                metadata = DocumentMetadata(
                    document_id=meta.document_id,
                    document_title=meta.document_title,
                    page_number=self._compress_pages(group_chunk["pages"]),
                    article_ref=article_ref,
                    section_ref=section_ref,
                    language=meta.language,
                    version_date=meta.version_date,
                    source_type=meta.source_type,
                    chunk_index=next_chunk_index,
                )
                chunks.append(
                    DocumentChunk(metadata=metadata, chunk_text=group_chunk["text"])
                )
                next_chunk_index += 1

        logger.info(
            "Chunking documentaire | source=%s | chunks=%s",
            structured.source_path,
            len(chunks),
        )
        return chunks

    def _group_pages_by_article(self, structured: StructuredPdfDocument) -> list[list]:
        groups: list[list] = []
        current: list = []
        current_article: str | None = None

        for page in structured.pages:
            article_ref = page.trace.article_ref
            if not current:
                current = [page]
                current_article = article_ref
                continue
            if article_ref == current_article:
                current.append(page)
                continue
            groups.append(current)
            current = [page]
            current_article = article_ref

        if current:
            groups.append(current)
        return groups

    def _build_text_blocks(self, pages: list) -> list[_TextBlock]:
        blocks: list[_TextBlock] = []
        for page in pages:
            for paragraph in self._split_into_paragraphs(page.text):
                blocks.extend(
                    _TextBlock(text=piece, page_number=page.trace.page_number)
                    for piece in self._split_oversized_paragraph(paragraph)
                )
        return blocks

    def _split_blocks(self, blocks: list[_TextBlock]) -> list[dict]:
        if not blocks:
            return []
        chunks: list[dict] = []
        current_blocks: list[_TextBlock] = []
        current_words = 0
        overlap_words: list[str] = []
        overlap_pages: set[int] = set()
        overlap_word_count = 0

        for block in blocks:
            block_words = self._word_count(block.text)
            max_body_words = max(1, self._max_words - overlap_word_count)
            projected = current_words + block_words

            if (
                current_blocks
                and projected > max_body_words
            ):
                chunks.append(
                    self._finalize_chunk(current_blocks, overlap_words, overlap_pages)
                )
                overlap_words = self._tail_words(
                    chunks[-1]["text"], max(1, int(self._max_words * self._overlap_ratio))
                )
                overlap_word_count = len(overlap_words)
                overlap_pages = {current_blocks[-1].page_number}
                current_blocks = []
                current_words = 0

            current_blocks.append(block)
            current_words += block_words

        if current_blocks:
            chunks.append(self._finalize_chunk(current_blocks, overlap_words, overlap_pages))
        return chunks

    def _finalize_chunk(
        self,
        blocks: list[_TextBlock],
        overlap_words: list[str],
        overlap_pages: set[int],
    ) -> dict:
        body_parts = [blk.text.strip() for blk in blocks if blk.text.strip()]
        body = "\n\n".join(body_parts).strip()
        pages = {blk.page_number for blk in blocks}

        if overlap_words:
            overlap = " ".join(overlap_words).strip()
            if overlap and not body.startswith(overlap):
                body = f"{overlap}\n\n{body}".strip()
            pages.update(overlap_pages)
        ordered_pages = sorted(pages)
        return {"text": body, "pages": ordered_pages}

    def _split_into_paragraphs(self, text: str) -> list[str]:
        parts = [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]
        if parts:
            return parts
        lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
        return lines

    def _split_oversized_paragraph(self, paragraph: str) -> list[str]:
        split_limit = self._max_body_words
        if self._word_count(paragraph) <= split_limit:
            return [paragraph]
        units = [u.strip() for u in re.split(r"(?<=[\.;:])\s+|\n+", paragraph) if u.strip()]
        if not units:
            units = [paragraph]

        pieces: list[str] = []
        current: list[str] = []
        current_words = 0
        for unit in units:
            unit_words = self._word_count(unit)
            if unit_words > split_limit:
                if current:
                    pieces.append(" ".join(current).strip())
                    current = []
                    current_words = 0
                pieces.extend(self._split_by_word_window(unit, split_limit))
                continue
            if current and current_words + unit_words > split_limit:
                pieces.append(" ".join(current).strip())
                current = [unit]
                current_words = unit_words
            else:
                current.append(unit)
                current_words += unit_words
        if current:
            pieces.append(" ".join(current).strip())
        return [piece for piece in pieces if piece]

    def _compress_pages(self, pages: list[int]) -> int | tuple[int, int]:
        ordered = sorted(set(pages))
        if len(ordered) == 1:
            return ordered[0]
        return (ordered[0], ordered[-1])

    def _word_count(self, text: str) -> int:
        return len(_WORD_RE.findall(text or ""))

    def _tail_words(self, text: str, n_words: int) -> list[str]:
        words = _WORD_RE.findall(text or "")
        if not words or n_words <= 0:
            return []
        return words[-n_words:]

    def _split_by_word_window(self, text: str, limit: int) -> list[str]:
        words = _WORD_RE.findall(text or "")
        if not words:
            return []
        return [" ".join(words[i : i + limit]) for i in range(0, len(words), limit)]

