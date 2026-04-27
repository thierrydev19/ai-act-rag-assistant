"""Détection conservative d'une référence d'article à partir du texte de page (lot 3).

Règles :
- uniquement une ligne dont le texte commencé après strip matche ``Article <numéro>`` ;
- exclusion des entrées de table des matières (lignes avec longues suites de points) ;
- si plusieurs numéros distincts apparaissent comme titres de ce type sur la même page,
  résultat indéterminé → ``None`` (pas d'invention) ;
- normalisation des espaces parasites intra-mot introduits par pypdf sur certains PDF
  (kerning extrait), uniquement pour la phase de détection : le texte source reste
  intact dans le reste du pipeline (chunking, embeddings).

``section_ref`` n'est pas dérivé ici : sur ce corpus PDF, aucun motif de section n'a été
jugé suffisamment fiable sans risque de faux positifs (voir doc lot 3 / tests).
"""

from __future__ import annotations

import re

# Titre d'article en tête de ligne (corps du règlement), pas "l'article 2" en milieu de phrase.
_LINE_LEADING_ARTICLE = re.compile(r"^(Article\s+(\d+[a-z]*))\b", re.IGNORECASE)
# Entrées type table : pointillés de suite
_TOC_LEADER_DOTS = re.compile(r"\.{8,}")
# Espaces parasites intra-mot (kerning pypdf) : 1 ou 2 lettres + espace + lettre.
# Exemple : "Ar ticle" -> "Article", "Maîtr ise" -> "Maîtrise", "har monisé" -> "harmonisé".
# On reste conservateur : uniquement entre lettres alphabétiques, jamais sur des chiffres.
_INTRA_WORD_SPACE = re.compile(r"(?<=[A-Za-zÀ-ÿ])\s(?=[A-Za-zÀ-ÿ])")


def _normalize_for_header_detection(line: str) -> str:
    """Lisse les espaces parasites intra-mot d'une ligne, à des fins de détection
    d'en-tête d'article uniquement. N'est appliqué qu'à la regex.

    Cette normalisation est volontairement agressive (elle transforme aussi
    les vrais espaces inter-mots de cette ligne), ce qui est acceptable parce
    que :
    1. on l'utilise UNIQUEMENT pour matcher un préfixe court "Article N" ;
    2. on ne l'écrit JAMAIS dans la trace ni dans le texte exposé ;
    3. la regex utilisée derrière n'a besoin que des 10 premiers caractères.
    """
    return _INTRA_WORD_SPACE.sub("", line)


def extract_article_ref_from_page_text(text: str) -> str | None:
    """Retourne une référence unique ``Article n`` ou ``None`` si non fiable."""
    numbers: list[str] = []
    for line in (text or "").split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        # 1) Tentative directe (PDF "propres", textes synthétiques, tests unitaires).
        match = _LINE_LEADING_ARTICLE.match(stripped)
        # 2) Si pas de match, tentative après normalisation des espaces parasites
        #    (typique des PDF EUR-Lex extraits par pypdf : "Ar ticle 4").
        if not match:
            normalized = _normalize_for_header_detection(stripped)
            match = _LINE_LEADING_ARTICLE.match(normalized)
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
