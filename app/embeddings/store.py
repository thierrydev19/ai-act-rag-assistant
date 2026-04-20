"""Stockage vectoriel Chroma pour le MVP (lot 5)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from app.document.models import DocumentChunk, DocumentMetadata
from app.embeddings.service import EmbeddingService
from app.logging.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """Store Chroma persistant pour indexer et relire les chunks du lot 4."""

    def __init__(
        self,
        *,
        persist_directory: str | Path = ".chroma",
        collection_name: str = "ai_act_mvp_chunks",
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self._persist_directory = Path(persist_directory)
        self._collection_name = collection_name
        self._persist_directory.mkdir(parents=True, exist_ok=True)
        self._embedding_service = embedding_service or EmbeddingService()
        self._client = chromadb.PersistentClient(
            path=str(self._persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(name=collection_name)

    def index(self, chunks: list[DocumentChunk]) -> None:
        """Indexe tous les chunks (échec explicite si un seul élément échoue)."""
        if not chunks:
            logger.info("Indexation ignorée: aucun chunk fourni.")
            return

        documents = [chunk.chunk_text for chunk in chunks]
        embeddings = self._embedding_service.embed_texts(documents)
        if len(embeddings) != len(chunks):
            raise RuntimeError("Echec embeddings: cardinalité incohérente.")

        ids = [self._chunk_id(chunk) for chunk in chunks]
        metadatas = [self._serialize_metadata(chunk.metadata) for chunk in chunks]

        try:
            self._collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
        except Exception as exc:  # pragma: no cover - couverture via tests d'échec
            msg = f"Echec indexation Chroma: {exc}"
            logger.error(msg)
            raise RuntimeError(msg) from exc

        logger.info("Indexation Chroma | chunks=%s", len(chunks))

    def reindex(self, chunks: list[DocumentChunk]) -> None:
        """Reindexe proprement le corpus en recreant la collection."""
        try:
            self._client.delete_collection(name=self._collection_name)
        except Exception:
            # Collection absente: aucun blocage, on recree juste ensuite.
            pass
        self._collection = self._client.get_or_create_collection(name=self._collection_name)
        self.index(chunks)

    def get_by_chunk_id(self, chunk_id: str) -> DocumentChunk:
        """Relit un chunk indexé, avec reconstruction des métadonnées source."""
        result = self._collection.get(
            ids=[chunk_id],
            include=["documents", "metadatas", "embeddings"],
        )
        ids = result.get("ids", [])
        if not ids:
            raise KeyError(f"Chunk introuvable: {chunk_id}")

        metadata_payload = result["metadatas"][0]
        document = result["documents"][0]
        metadata = self._deserialize_metadata(metadata_payload)
        return DocumentChunk(metadata=metadata, chunk_text=document)

    def get_embedding_by_chunk_id(self, chunk_id: str) -> list[float]:
        """Retourne l'embedding stocké pour un chunk indexé."""
        result = self._collection.get(ids=[chunk_id], include=["embeddings"])
        ids = result.get("ids", [])
        if not ids:
            raise KeyError(f"Chunk introuvable: {chunk_id}")
        embedding = result["embeddings"][0]
        return [float(v) for v in embedding]

    def search(
        self,
        *,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Recherche les chunks les plus proches pour un embedding donné."""
        if top_k <= 0:
            raise ValueError("top_k doit etre strictement positif.")
        if not query_embedding:
            raise ValueError("query_embedding vide.")

        try:
            result = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            msg = f"Echec recherche Chroma: {exc}"
            logger.error(msg)
            raise RuntimeError(msg) from exc

        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        hits: list[dict[str, Any]] = []
        for chunk_id, doc, metadata_payload, distance in zip(
            ids, docs, metas, distances, strict=False
        ):
            if metadata_payload is None or doc is None:
                continue
            hits.append(
                {
                    "chunk_id": chunk_id,
                    "distance": float(distance),
                    "chunk": DocumentChunk(
                        metadata=self._deserialize_metadata(metadata_payload),
                        chunk_text=doc,
                    ),
                }
            )
        return hits

    def _chunk_id(self, chunk: DocumentChunk) -> str:
        meta = chunk.metadata
        return f"{meta.document_id}:{meta.chunk_index}"

    def _serialize_metadata(self, metadata: DocumentMetadata) -> dict[str, Any]:
        payload = {
            "document_id": metadata.document_id,
            "document_title": metadata.document_title,
            "page_number": self._serialize_page_number(metadata.page_number),
            "article_ref": metadata.article_ref,
            "section_ref": metadata.section_ref,
            "language": metadata.language,
            "version_date": metadata.version_date,
            "source_type": metadata.source_type,
            "chunk_index": metadata.chunk_index,
        }
        return {
            "document_id": metadata.document_id,
            "chunk_index": metadata.chunk_index,
            "embedding_strategy": self._embedding_service.strategy,
            "metadata_json": json.dumps(payload, ensure_ascii=True, separators=(",", ":")),
        }

    def _deserialize_metadata(self, payload: dict[str, Any]) -> DocumentMetadata:
        if "metadata_json" not in payload:
            raise RuntimeError("metadata_json absent dans l'enregistrement indexe.")
        raw = json.loads(payload["metadata_json"])
        return DocumentMetadata(
            document_id=str(raw["document_id"]),
            document_title=str(raw["document_title"]),
            page_number=self._deserialize_page_number(raw["page_number"]),
            article_ref=raw["article_ref"],
            section_ref=raw["section_ref"],
            language=str(raw["language"]),
            version_date=str(raw["version_date"]),
            source_type=str(raw["source_type"]),
            chunk_index=int(raw["chunk_index"]),
        )

    def _serialize_page_number(self, value: int | tuple[int, int]) -> str:
        if isinstance(value, int):
            return str(value)
        return f"{value[0]}-{value[1]}"

    def _deserialize_page_number(self, value: str) -> int | tuple[int, int]:
        if "-" not in value:
            return int(value)
        left, right = value.split("-", maxsplit=1)
        return (int(left), int(right))

