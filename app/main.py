"""Point d'entrée applicatif du socle MVP (lot 1)."""

from dataclasses import dataclass

from app.ui.app import build_ui


@dataclass(frozen=True)
class AppBootstrap:
    """Indique les modules structurants prêts pour les lots suivants."""

    ingestion: str = "ready"
    document: str = "ready"
    chunking: str = "ready"
    embeddings: str = "ready"
    retrieval: str = "ready"
    generation: str = "ready"
    ui: str = "ready"
    logging: str = "ready"


def bootstrap() -> AppBootstrap:
    """Construit un état minimal de démarrage sans pipeline réel."""
    _ = build_ui()
    return AppBootstrap()

