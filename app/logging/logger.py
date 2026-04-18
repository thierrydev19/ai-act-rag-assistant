"""Configuration de logs simple pour le socle MVP."""

import logging


def get_logger(name: str = "ai_act_rag") -> logging.Logger:
    """Crée un logger standard console pour les prochains lots."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

