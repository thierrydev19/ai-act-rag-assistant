"""Détection conservative d'une référence d'article à partir du texte de page (lot 3).

Règles :
- uniquement une ligne dont le texte commencé après strip matche ``Article <numéro>`` ;
- exclusion des entrées de table des matières (lignes avec longues suites de points) ;
- si plusieurs numéros distincts apparaissent comme titres de ce type sur la même page,
  résultat indéterminé → ``None`` (pas d'invention).

``section_ref`` n'est pas dérivé ici : sur ce corpus PDF, aucun motif de section n'a été
jugé suffisamment fiable sans risque de faux positifs (voir doc lot 3 / tests).
"""

from __future__ import annotations

import re

# Titre d'article en tête de ligne (corps du règlement), pas "l'article 2" en milieu de phrase.
_LINE_LEADING_ARTICLE = re.compile(r"^(Article\s+(\d+[a-z]*))\b", re.IGNORECASE)
# Entrées type table : pointillés de suite
_TOC_LEADER_DOTS = re.compile(r"\.{8,}")


def extract_article_ref_from_page_text(text: str) -> str | None:
    """Retourne une référence unique ``Article n`` ou ``None`` si non fiable."""
    numbers: list[str] = []
    for line in (text or "").split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        match = _LINE_LEADING_ARTICLE.match(stripped)
        if not match:
            continue
        if _TOC_LEADER_DOTS.search(stripped):
            continue
        numbers.append(match.group(2).lower())
    if not numbers:
        return None
    distinct = set(numbers)
    if len(distinct) != 1:
        return None
    token = numbers[0]
    if token.isdigit():
        return f"Article {int(token)}"
    return f"Article {token}"


def extract_section_ref_from_page_text(text: str) -> str | None:
    """Réservé : aucune extraction fiable activée dans le périmètre lot 3."""
    _ = text
    return None
