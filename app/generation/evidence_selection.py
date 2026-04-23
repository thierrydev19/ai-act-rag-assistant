"""Selection legere des extraits utiles avant generation."""

from __future__ import annotations

from dataclasses import dataclass
import re

from app.document.models import DocumentChunk

_WORD_RE = re.compile(r"\w+", re.UNICODE)


@dataclass(frozen=True)
class EvidenceSelection:
    """Resultat de la selection d'extraits pour la generation."""

    core_chunks: list[DocumentChunk]
    secondary_chunks: list[DocumentChunk]
    rejected_chunks: list[DocumentChunk]
    is_coherent: bool
    intent_aligned: bool
    message: str


class EvidenceSelector:
    """Classement simple et explicable des extraits recuperes."""

    def __init__(self, *, max_core: int = 2, min_score: float = 0.06) -> None:
        self._max_core = max_core
        self._min_score = min_score

    def select(
        self,
        *,
        question_text: str,
        chunks: list[DocumentChunk],
        intent: str = "limites_conclusion",
    ) -> EvidenceSelection:
        if not chunks:
            return EvidenceSelection(
                core_chunks=[],
                secondary_chunks=[],
                rejected_chunks=[],
                is_coherent=False,
                intent_aligned=False,
                message="Aucun extrait disponible apres retrieval.",
            )
        question_tokens = self._question_tokens(question_text)
        scored: list[tuple[float, DocumentChunk]] = []
        for chunk in chunks:
            score = self._score_chunk(question_tokens=question_tokens, chunk=chunk, intent=intent)
            scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)

        core: list[DocumentChunk] = [chunk for score, chunk in scored if score >= self._min_score][: self._max_core]
        if not core and scored and self._is_domain_question(question_tokens):
            best_score, best_chunk = scored[0]
            if best_score >= 0.03:
                core = [best_chunk]
        if not core:
            return EvidenceSelection(
                core_chunks=[],
                secondary_chunks=[],
                rejected_chunks=[chunk for _, chunk in scored],
                is_coherent=False,
                intent_aligned=False,
                message=(
                    "Aucun noyau documentaire coherent n'a ete detecte: les extraits "
                    "sont trop eloignes ou trop faibles pour soutenir une reponse fiable."
                ),
            )

        remaining = [chunk for _, chunk in scored if chunk not in core]
        secondary = remaining[:2]
        rejected = remaining[2:]
        coherence = self._is_coherent(question_tokens=question_tokens, core_chunks=core)
        aligned = self._is_intent_aligned(intent=intent, core_chunks=core)
        return EvidenceSelection(
            core_chunks=core,
            secondary_chunks=secondary,
            rejected_chunks=rejected,
            is_coherent=coherence,
            intent_aligned=aligned,
            message=(
                "Noyau documentaire coherent et aligne avec l'intention detectee."
                if coherence and aligned
                else (
                    "Extraits trop disperses pour soutenir une reponse fiable."
                    if not coherence
                    else "Noyau documentaire insuffisamment aligne avec l'intention de la question."
                )
            ),
        )

    def _score_chunk(self, *, question_tokens: set[str], chunk: DocumentChunk, intent: str) -> float:
        chunk_tokens = {token.lower() for token in _WORD_RE.findall(chunk.chunk_text) if len(token) >= 4}
        if not chunk_tokens:
            return 0.0
        overlap = question_tokens.intersection(chunk_tokens)
        overlap_ratio = len(overlap) / max(len(question_tokens), 1)
        thematic_overlap = self._theme_tokens(question_tokens).intersection(self._theme_tokens(chunk_tokens))
        thematic_bonus = 0.08 if thematic_overlap else 0.0
        verifier_bonus = 0.0
        if "verifier" in question_tokens and any(
            token in chunk_tokens for token in ("transparence", "informations", "documentation", "preuves")
        ):
            verifier_bonus = 0.05

        text = chunk.chunk_text.lower()
        intent_markers = (
            "obligation",
            "transparence",
            "documentation",
            "preuve",
            "informations",
            "qualif",
            "fournisseur",
            "deployeur",
            "haut risque",
            "high-risk",
        )
        marker_bonus = 0.02 * sum(1 for marker in intent_markers if marker in text) if overlap_ratio > 0 else 0.0
        sanction_penalty = 0.0
        if "sanction" in text and "sanctions" not in question_tokens and "sanction" not in question_tokens:
            sanction_penalty = -0.03
        intent_bonus, intent_penalty = self._intent_signal_adjustment(intent=intent, chunk_tokens=chunk_tokens, text=text)

        # Bonus faible pour references structurees (plus exploitables en demo).
        ref_bonus = 0.03 if chunk.metadata.article_ref else 0.0
        return (
            overlap_ratio
            + thematic_bonus
            + verifier_bonus
            + marker_bonus
            + ref_bonus
            + sanction_penalty
            + intent_bonus
            + intent_penalty
        )

    def _is_coherent(self, *, question_tokens: set[str], core_chunks: list[DocumentChunk]) -> bool:
        if not core_chunks:
            return False
        if len(core_chunks) == 1:
            return True
        if len(core_chunks) <= 2 and all(chunk.metadata.article_ref for chunk in core_chunks):
            return True
        if any(
            question_tokens.intersection(
                {token.lower() for token in _WORD_RE.findall(chunk.chunk_text) if len(token) >= 4}
            )
            for chunk in core_chunks
        ):
            return True
        token_sets = [
            {token.lower() for token in _WORD_RE.findall(chunk.chunk_text) if len(token) >= 4}
            for chunk in core_chunks
        ]
        common = set.intersection(*token_sets) if token_sets else set()
        if common.intersection(question_tokens):
            return True
        theme_sets = [self._theme_tokens(tokens) for tokens in token_sets]
        common_themes = set.intersection(*theme_sets) if theme_sets else set()
        if common_themes:
            return True
        # Accepter un noyau a 2 extraits avec theme commun minimal.
        thematic = {"obligation", "transparence", "documentation", "fournisseur", "deployeur", "risque"}
        return bool(common.intersection(thematic))

    def _question_tokens(self, question_text: str) -> set[str]:
        return {token.lower() for token in _WORD_RE.findall(question_text or "") if len(token) >= 4}

    def _is_domain_question(self, question_tokens: set[str]) -> bool:
        domain = {
            "obligation",
            "obligations",
            "transparence",
            "systeme",
            "documentation",
            "preuves",
            "qualifier",
            "qualification",
            "conformite",
            "fournisseur",
            "deployeur",
            "risque",
            "chatbot",
            "utilisateurs",
            "service",
            "client",
            "verifier",
            "recrutement",
            "candidats",
        }
        return bool(question_tokens.intersection(domain))

    def _theme_tokens(self, tokens: set[str]) -> set[str]:
        themes: set[str] = set()
        mapping = {
            "transparence": "transparence",
            "informations": "transparence",
            "utilisateur": "transparence",
            "utilisateurs": "transparence",
            "obligation": "obligations",
            "obligations": "obligations",
            "documentation": "documentation",
            "documents": "documentation",
            "preuves": "documentation",
            "traces": "documentation",
            "logs": "documentation",
            "fournisseur": "role",
            "provider": "role",
            "deployeur": "role",
            "deployer": "role",
            "risque": "risque",
            "qualifier": "qualification",
            "qualification": "qualification",
            "verifier": "verification",
            "chatbot": "service_client",
            "client": "service_client",
            "service": "service_client",
        }
        for token in tokens:
            if token in mapping:
                themes.add(mapping[token])
        return themes

    def _is_intent_aligned(self, *, intent: str, core_chunks: list[DocumentChunk]) -> bool:
        if not core_chunks:
            return False
        if intent == "limites_conclusion":
            return True
        expected, penalized = self._intent_signals(intent)
        matched = 0
        strong_mismatch = 0
        for chunk in core_chunks:
            tokens = {token.lower() for token in _WORD_RE.findall(chunk.chunk_text) if len(token) >= 4}
            text = chunk.chunk_text.lower()
            has_expected = any(signal in text or signal in tokens for signal in expected)
            has_penalized = any(signal in text or signal in tokens for signal in penalized)
            if has_expected:
                matched += 1
            if has_penalized and not has_expected:
                strong_mismatch += 1
        if strong_mismatch >= 1 and matched == 0:
            return False
        return matched >= 1

    def _intent_signal_adjustment(
        self, *, intent: str, chunk_tokens: set[str], text: str
    ) -> tuple[float, float]:
        expected, penalized = self._intent_signals(intent)
        has_expected = any(signal in text or signal in chunk_tokens for signal in expected)
        has_penalized = any(signal in text or signal in chunk_tokens for signal in penalized)
        bonus = 0.12 if has_expected else 0.0
        penalty = -0.10 if (has_penalized and not has_expected) else 0.0
        return bonus, penalty

    def _intent_signals(self, intent: str) -> tuple[set[str], set[str]]:
        by_intent = {
            "qualification_systeme": (
                {"definition", "qualif", "perimetre", "annexe", "high", "risque", "usage", "finalite"},
                {"transparence", "utilisateur", "informations"},
            ),
            "transparence_information": (
                {"transparence", "utilisateur", "informations", "interaction"},
                {"documentation technique", "organisme notifie", "certification"},
            ),
            "documentation_preuves": (
                {"documentation", "instructions", "qualite", "logs", "traces", "preuve", "conformite"},
                {"transparence", "utilisateur"},
            ),
            "obligations_entreprise": (
                {"obligation", "responsabil", "mesures", "entreprise", "fournisseur", "deployeur"},
                {"annexe", "certification"},
            ),
            "role_entreprise": (
                {"fournisseur", "deployeur", "importateur", "distributeur", "role"},
                {"transparence", "documentation technique"},
            ),
            "applicability_perimetre": (
                {"champ", "application", "exclusion", "perimetre", "concerne"},
                {"obligations detaillees", "documentation technique"},
            ),
        }
        default = ({"obligation", "transparence", "documentation"}, set())
        return by_intent.get(intent, default)

