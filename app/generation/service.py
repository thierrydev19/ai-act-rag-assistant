"""Service de generation contrainte par sources (lot 7)."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal

from app.document.models import UserQuestion
from app.generation.evidence_selection import EvidenceSelection, EvidenceSelector
from app.retrieval.service import RetrievalResult
from app.logging.logger import get_logger

logger = get_logger(__name__)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_RE = re.compile(r"\w+", re.UNICODE)


@dataclass(frozen=True)
class AnswerPayload:
    """Charge utile de réponse côté application."""

    answer_text: str
    citations: list[str]
    refusal: bool
    intent: str
    business_case: str


class GenerationService:
    """Construit une reponse professionnelle strictement bornee aux sources."""

    def __init__(self, *, max_citations: int = 3) -> None:
        if max_citations <= 0:
            raise ValueError("max_citations doit etre strictement positif.")
        self._max_citations = max_citations
        self._min_overlap_ratio = 0.05
        self._selector = EvidenceSelector(max_core=2)

    def generate(self, question: UserQuestion, context: RetrievalResult) -> AnswerPayload:
        """Genere une reponse contrainte avec citations ou refus explicite."""
        intent = self._classify_intent(question.text)
        business_case = self._classify_business_case(question.text)
        if self._is_out_of_scope_question(question.text):
            refusal = self._build_refusal(
                context_message=(
                    "Question hors perimetre documentaire (domaine non couvert ou demande "
                    "de conseil strategique / avis juridique definitif)."
                )
            )
            return AnswerPayload(
                answer_text=refusal,
                citations=[],
                refusal=True,
                intent="limites_conclusion",
                business_case="generic",
            )
        if not context.is_sufficient or not context.chunks:
            refusal = self._build_refusal(context_message=context.message)
            return AnswerPayload(
                answer_text=refusal,
                citations=[],
                refusal=True,
                intent="limites_conclusion",
                business_case="generic",
            )
        if self._looks_like_semantic_false_positive(question.text, context):
            refusal = self._build_refusal(
                context_message=(
                    "Les extraits recuperes semblent semantiquement voisins, mais trop "
                    "faiblement relies a la question pour conclure de maniere fiable."
                )
            )
            return AnswerPayload(
                answer_text=refusal,
                citations=[],
                refusal=True,
                intent="limites_conclusion",
                business_case=business_case,
            )

        selection = self._selector.select(
            question_text=question.text,
            chunks=context.chunks,
            intent=intent,
        )
        if not selection.core_chunks:
            refusal = self._build_refusal(context_message=selection.message)
            return AnswerPayload(
                answer_text=refusal,
                citations=[],
                refusal=True,
                intent=intent,
                business_case=business_case,
            )
        if not selection.is_coherent:
            refusal = self._build_refusal(context_message=selection.message)
            return AnswerPayload(
                answer_text=refusal,
                citations=[],
                refusal=True,
                intent=intent,
                business_case=business_case,
            )
        if not selection.intent_aligned:
            refusal = self._build_refusal(
                context_message=(
                    "Les extraits recuperes ne sont pas suffisamment alignes avec l'intention "
                    "de la question pour produire une reponse fiable et centree."
                )
            )
            return AnswerPayload(
                answer_text=refusal,
                citations=[],
                refusal=True,
                intent=intent,
                business_case=business_case,
            )
        selected_chunks = (selection.core_chunks + selection.secondary_chunks)[: self._max_citations]
        citations = [self._format_citation(c) for c in selected_chunks]
        answer_text = self._build_grounded_answer(
            question=question,
            selected=selection,
            citations=citations,
            intent=intent,
            business_case=business_case,
        )
        return AnswerPayload(
            answer_text=answer_text,
            citations=citations,
            refusal=False,
            intent=intent,
            business_case=business_case,
        )

    def build_constrained_prompt(self, question: UserQuestion, context: RetrievalResult) -> str:
        """Construit un prompt strictement borne aux extraits retrouves."""
        chunks = context.chunks[: self._max_citations]
        if not chunks:
            chunks_block = "Aucun extrait."
        else:
            lines: list[str] = []
            for idx, chunk in enumerate(chunks, start=1):
                lines.append(f"[EXTRAIT {idx}] {self._format_citation(chunk)}")
                lines.append(chunk.chunk_text.strip())
            chunks_block = "\n".join(lines)
        return (
            "Tu reponds uniquement avec les informations presentes dans les extraits ci-dessous.\n"
            "Interdits: invention, extrapolation juridique definitive, ajout de source externe.\n"
            "Si information insuffisante: refuser explicitement.\n"
            "Format impose:\n"
            "1. Reponse simple\n"
            "2. Ce que cela veut dire pour votre entreprise\n"
            "3. Ce qu'il faut verifier\n"
            "4. Ce qui reste incertain\n"
            "5. Sources\n"
            "6. Limites\n\n"
            f"Question: {question.text.strip()}\n\n"
            f"Extraits:\n{chunks_block}"
        )

    def _build_grounded_answer(
        self,
        *,
        question: UserQuestion,
        selected: EvidenceSelection,
        citations: list[str],
        intent: str,
        business_case: str,
    ) -> str:
        highlights = self._extract_highlights(question.text, selected.core_chunks)
        answer_simple = self._build_answer_simple(intent=intent, highlights=highlights)
        business_impact = self._build_business_impact(
            intent=intent,
            business_case=business_case,
            highlights=highlights,
            question_text=question.text,
            selected=selected,
        )
        checks = self._build_checks(
            intent=intent,
            business_case=business_case,
            highlights=highlights,
            question_text=question.text,
            selected=selected,
        )
        uncertainties = self._build_uncertainties(
            intent=intent,
            business_case=business_case,
            highlights=highlights,
            selected=selected,
            question_text=question.text,
        )
        sources = "\n".join(f"- {c}" for c in citations)
        limits = self._build_limits(
            intent=intent,
            business_case=business_case,
            question_text=question.text,
            selected=selected,
        )
        return (
            "1. Reponse simple\n"
            f"{answer_simple}\n\n"
            "2. Ce que cela veut dire pour votre entreprise\n"
            f"{business_impact}\n\n"
            "3. Ce qu'il faut verifier\n"
            f"{checks}\n\n"
            "4. Ce qui reste incertain\n"
            f"{uncertainties}\n\n"
            "5. Sources\n"
            f"{sources}\n\n"
            "6. Limites\n"
            f"{limits}"
        )

    def _build_refusal(self, *, context_message: str) -> str:
        return (
            "1. Reponse simple\n"
            "Je ne peux pas conclure de maniere fiable a partir du corpus charge pour cette question.\n\n"
            "2. Ce que cela veut dire pour votre entreprise\n"
            "- Vous ne devez pas prendre une decision de conformite uniquement sur cette base.\n\n"
            "3. Ce qu'il faut verifier\n"
            f"- Cause principale: {context_message}\n"
            "- Reformuler la question ou enrichir le corpus/documentation avant toute conclusion.\n\n"
            "4. Ce qui reste incertain\n"
            "- Le corpus actuel ne permet pas d'etablir une position fiable pour votre cas.\n\n"
            "5. Sources\n"
            "- Aucune source suffisamment pertinente n'a pu etre retenue.\n\n"
            "6. Limites\n"
            "- Cette reponse ne constitue pas un avis juridique definitif.\n"
            "- Sans base documentaire suffisante, toute conclusion serait speculative."
        )

    def _extract_highlights(self, question_text: str, chunks: list) -> list[str]:
        keywords = {
            token.lower()
            for token in _WORD_RE.findall(question_text or "")
            if len(token) >= 4
        }
        highlights: list[str] = []
        for chunk in chunks[:2]:
            sentences = _SENTENCE_SPLIT_RE.split(chunk.chunk_text.strip())
            chosen = None
            for sentence in sentences:
                sentence_tokens = {t.lower() for t in _WORD_RE.findall(sentence)}
                if keywords and sentence_tokens.intersection(keywords):
                    chosen = sentence.strip()
                    break
            if chosen is None and sentences:
                chosen = sentences[0].strip()
            if chosen:
                citation = self._format_citation(chunk)
                highlights.append(f"{chosen} ({citation})")
        return highlights

    def _looks_like_semantic_false_positive(
        self, question_text: str, context: RetrievalResult
    ) -> bool:
        text = (question_text or "").lower()
        in_domain_markers = (
            "ai act",
            "ia",
            "obligation",
            "transparence",
            "qualif",
            "systeme",
            "documentation",
            "preuve",
            "fournisseur",
            "deployeur",
            "importateur",
            "conformite",
            "surveillance",
            "biometr",
            "scoring",
            "service client",
            "chatbot",
            "recrutement",
            "candidat",
            "verifier",
        )
        text_tokens = {token.lower() for token in _WORD_RE.findall(text)}
        if any(
            (marker in text if " " in marker else marker in text_tokens)
            for marker in in_domain_markers
        ):
            return False
        question_tokens = {
            token.lower()
            for token in _WORD_RE.findall(question_text or "")
            if len(token) >= 5
        }
        if len(question_tokens) <= 2:
            return False
        if not question_tokens:
            return False
        corpus_tokens: set[str] = set()
        for chunk in context.chunks[: self._max_citations]:
            corpus_tokens.update(
                token.lower() for token in _WORD_RE.findall(chunk.chunk_text) if len(token) >= 5
            )
        if not corpus_tokens:
            return True
        overlap = question_tokens.intersection(corpus_tokens)
        overlap_ratio = len(overlap) / len(question_tokens)
        return overlap_ratio < self._min_overlap_ratio

    def _format_citation(self, chunk) -> str:
        meta = chunk.metadata
        page = self._format_page(meta.page_number)
        if meta.article_ref and meta.section_ref:
            return f"AI Act - {meta.article_ref} - Section {meta.section_ref} - page {page}"
        if meta.article_ref:
            return f"AI Act - {meta.article_ref} - page {page}"
        if meta.section_ref:
            return f"AI Act - Section {meta.section_ref} - page {page}"
        return f"AI Act - page {page}"

    def _format_page(self, page_number: int | tuple[int, int]) -> str:
        if isinstance(page_number, int):
            return str(page_number)
        return f"{page_number[0]}-{page_number[1]}"

    def _is_out_of_scope_question(self, question_text: str) -> bool:
        text = (question_text or "").lower()
        out_of_scope_markers = (
            "avis juridique definitif",
            "strategie commerciale",
            "meilleur choix de fournisseur",
            "hors ai act",
            "regime fiscal",
            "fiscalite",
            "fiscal",
            "impot",
            "tva",
            "droit du travail",
            "rgpd",
            "gdpr",
            "propriete intellectuelle",
            "brevets",
            "comptabilite",
            "douane",
            "droit penal",
        )
        return any(marker in text for marker in out_of_scope_markers)

    def _classify_intent(
        self, question_text: str
    ) -> Literal[
        "applicability_perimetre",
        "qualification_systeme",
        "obligations_entreprise",
        "transparence_information",
        "documentation_preuves",
        "role_entreprise",
        "limites_conclusion",
    ]:
        text = (question_text or "").lower()
        if any(word in text for word in ("applicable", "perimetre", "concerne")):
            return "applicability_perimetre"
        if any(word in text for word in ("definition", "qualif", "systeme ia")):
            return "qualification_systeme"
        if any(word in text for word in ("transparence", "informer", "information")):
            return "transparence_information"
        if any(word in text for word in ("obligation", "doit", "conformite")):
            return "obligations_entreprise"
        if any(word in text for word in ("documentation", "preuve", "trace")):
            return "documentation_preuves"
        if any(word in text for word in ("fournisseur", "deployeur", "importateur", "role")):
            return "role_entreprise"
        return "limites_conclusion"

    def _build_answer_simple(self, *, intent: str, highlights: list[str]) -> str:
        if not highlights:
            return (
                "Les extraits donnent une orientation partielle, sans permettre une conclusion "
                "definitive pour votre cas."
            )
        first = highlights[0].split(" (AI Act - ", maxsplit=1)[0]
        by_intent = {
            "applicability_perimetre": "Les extraits indiquent surtout comment verifier si votre cas entre dans le perimetre AI Act.",
            "qualification_systeme": "Les extraits donnent des criteres utiles pour qualifier votre systeme, sans trancher a eux seuls.",
            "obligations_entreprise": "Les extraits pointent des obligations a organiser dans l'entreprise selon votre role.",
            "transparence_information": "Les extraits confirment des attentes de transparence envers les utilisateurs.",
            "documentation_preuves": "Les extraits insistent sur la documentation et les preuves a conserver.",
            "role_entreprise": "Les extraits aident a clarifier vos responsabilites selon votre position dans la chaine IA.",
            "limites_conclusion": "Les extraits donnent des elements utiles, mais incomplets pour statuer.",
        }
        return f"{by_intent.get(intent, by_intent['limites_conclusion'])} Point saillant: {first}"

    def _build_business_impact(
        self,
        *,
        intent: str,
        business_case: str,
        highlights: list[str],
        question_text: str,
        selected: EvidenceSelection,
    ) -> str:
        if not highlights:
            return "- Vous devez traiter ce sujet comme un point a clarifier avant toute decision operationnelle."
        by_intent = {
            "applicability_perimetre": "- En pratique, le premier enjeu est de confirmer que votre usage entre bien dans le champ du reglement avant de deriver des obligations.",
            "qualification_systeme": "- Pour votre entreprise, l'etape cle est de qualifier l'usage reel du systeme avant de discuter d'obligations detaillees.",
            "obligations_entreprise": "- L'effet concret pour votre entreprise est de structurer les verifications par role, usage et niveau de risque plutot que d'appliquer une liste unique.",
            "transparence_information": "- Concretement, vous devez surtout definir quelles informations seront donnees aux personnes exposees a l'IA et a quel moment.",
            "documentation_preuves": "- L'enjeu pratique est d'organiser des preuves exploitables (documents, traces, instructions) en lien avec votre usage reel.",
            "role_entreprise": "- Le point cle est de clarifier votre place dans la chaine de valeur, car les responsabilites evoluent selon ce role.",
            "limites_conclusion": "- A ce stade, les sources permettent un cadrage utile, mais pas une position finale applicable sans verifications complementaires.",
        }
        by_business_case = {
            "rh_recrutement": "- Pour le recrutement, commencez par cadrer les etapes ou l'IA influence une decision individuelle et les controles associes.",
            "service_client": "- Pour le service client, priorisez la clarte sur le role de l'IA et l'organisation d'un traitement des contestations.",
            "biometrie_surveillance_controle_acces": "- Pour un usage biometrie/surveillance/controle d'acces, la robustesse du cadrage et des preuves devient determinante.",
            "scoring_decision_automatisee": "- Pour le scoring/decision automatisee, la tracabilite des criteres et l'intervention humaine doivent etre explicites.",
            "generic": "- Pour avancer utilement, transformez ces points en verifications operationnelles adaptees a votre contexte.",
        }
        baseline = (
            by_intent.get(intent, by_intent["limites_conclusion"])
            + "\n"
            + by_business_case[business_case]
        )
        if intent == "obligations_entreprise":
            role_signals = self._role_signals(selected.core_chunks)
            risk_signals = self._document_signals(selected.core_chunks)
            role_clause = f" ({role_signals})" if role_signals else ""
            return (
                "- Vos obligations dependent d'abord de votre role exact dans la chaine de valeur (fournisseur, deployeur, importateur, autre).\n"
                f"- A ce stade, les sources retenues suggerent surtout un cadrage par role{role_clause} et par niveau de risque potentiel.\n"
                + (
                    "- Si un usage high-risk est confirme, la structuration des obligations (documentation, supervision, gouvernance) devient plus exigeante."
                    if risk_signals["high_risk"]
                    else "- Si la qualification high-risk n'est pas etablie, il faut traiter ces obligations comme des familles a verifier, pas comme une liste universelle."
                )
            )
        if self._is_document_request(question_text):
            doc_signals = self._document_signals(selected.core_chunks)
            if doc_signals["high_risk"]:
                return (
                    baseline
                    + "\n- Si votre cas releve d'un usage high-risk et selon votre role, une preparation documentaire plus structuree est probablement necessaire."
                )
            return (
                baseline
                + "\n- A ce stade, le corpus retenu confirme surtout un besoin de verification ciblee, sans permettre d'imposer un dossier documentaire universel."
            )
        return baseline

    def _build_checks(
        self,
        *,
        intent: str,
        business_case: str,
        highlights: list[str],
        question_text: str,
        selected: EvidenceSelection,
    ) -> str:
        if intent == "obligations_entreprise":
            return self._build_obligations_checks(selected=selected)
        if self._is_document_request(question_text):
            return self._build_document_factual_checks(selected=selected)
        checks: list[str] = [
            "- Verifier que votre cas reel correspond bien au perimetre des extraits cites.",
            "- Confirmer votre role (fournisseur, deployeur, autre) avant de deduire des obligations.",
        ]
        if intent in {"qualification_systeme", "applicability_perimetre"}:
            checks.append("- Documenter les faits techniques et d'usage necessaires a la qualification.")
        if business_case == "rh_recrutement":
            checks.append("- Verifier les etapes ou l'IA influence une decision RH individuelle.")
        if business_case == "service_client":
            checks.append("- Verifier comment l'utilisateur est informe qu'il interagit avec une IA.")
        if business_case == "biometrie_surveillance_controle_acces":
            checks.append("- Verifier les conditions d'usage, le contexte et les garde-fous operationnels.")
        if business_case == "scoring_decision_automatisee":
            checks.append("- Verifier l'existence d'un controle humain sur les decisions sensibles.")
        if highlights:
            checks.append("- Relire les sources citees pour valider les termes exacts applicables a votre situation.")
        return "\n".join(checks[:4])

    def _build_obligations_checks(self, *, selected: EvidenceSelection) -> str:
        doc_signals = self._document_signals(selected.core_chunks)
        role_hint = self._role_signals(selected.core_chunks)
        lines = [
            "- Role de l'entreprise: verifier en priorite si vous agissez comme fournisseur, deployeur, importateur ou simple utilisateur d'un outil tiers.",
            "- Type de systeme et contexte d'usage: verifier si votre cas releve d'une obligation de transparence seule ou d'un cadre potentiellement high-risk.",
            "- Familles d'obligations a verifier: information/transparence, documentation/preuves, supervision/controle et gouvernance interne.",
            "- Conditions avant conclusion: role exact, qualification du systeme, niveau de risque et contexte operationnel doivent etre etablis avant toute conclusion ferme.",
        ]
        if role_hint:
            lines[0] = f"- Role de l'entreprise: les sources pointent {role_hint}; verifier ce role en pratique avant de figer les obligations."
        if doc_signals["high_risk"]:
            lines[2] = (
                "- Familles d'obligations a verifier: en cas high-risk possible, verifier particulierement documentation technique, traces, supervision et exigences de controle associees."
            )
        return "\n".join(lines)

    def _build_uncertainties(
        self,
        *,
        intent: str,
        business_case: str,
        highlights: list[str],
        selected: EvidenceSelection,
        question_text: str,
    ) -> str:
        notes: list[str] = []
        by_intent = {
            "applicability_perimetre": "- Le corpus ne permet pas encore de trancher completement la frontiere entre cas couvert et cas exclu pour votre situation.",
            "qualification_systeme": "- La qualification depend encore de faits d'usage (finalite, autonomie, contexte de decision) non totalement etablis ici.",
            "obligations_entreprise": "- La priorite exacte des obligations depend du role reel de votre entreprise et du niveau de risque effectivement retenu.",
            "transparence_information": "- Les modalites exactes d'information (moment, contenu detaille, destinataires) dependent de votre parcours utilisateur concret.",
            "documentation_preuves": "- Le niveau de preuve attendu varie selon la qualification et le role, ce que les extraits ne figent pas integralement pour votre cas.",
            "role_entreprise": "- Les responsabilites precises restent conditionnees par votre position contractuelle effective dans la chaine de valeur.",
            "limites_conclusion": "- Les extraits permettent un cadrage, mais pas une conclusion exhaustive sur tous les points de votre situation.",
        }
        notes.append(by_intent.get(intent, by_intent["limites_conclusion"]))
        notes.append("- Certains faits operationnels necessaires (organisation interne, perimetre exact, niveau de risque) ne sont pas fournis dans la question.")
        if intent == "role_entreprise":
            notes.append("- La repartition exacte des responsabilites depend de vos contrats et de la chaine de valeur.")
        if business_case in {"biometrie_surveillance_controle_acces", "scoring_decision_automatisee"}:
            notes.append("- Les impacts concrets varient fortement selon le contexte d'usage et le niveau de risque retenu.")
        if self._is_document_request(question_text):
            doc_signals = self._document_signals(selected.core_chunks)
            if not doc_signals["high_risk"]:
                notes.append("- Le corpus retenu ne permet pas d'affirmer que des documents high-risk sont obligatoires pour votre cas.")
            if not doc_signals["provider_or_deployer"]:
                notes.append("- Le role exact de votre entreprise n'est pas suffisamment etabli pour figer la liste des livrables.")
        if not highlights:
            notes.append("- L'absence de points saillants robustes reduit le niveau de confiance de la synthese.")
        return "\n".join(notes[:3])

    def _build_limits(
        self,
        *,
        intent: str,
        business_case: str,
        question_text: str,
        selected: EvidenceSelection,
    ) -> str:
        _ = (intent, business_case)
        lines = ["- Cette reponse est informative et ne constitue pas un avis juridique definitif."]
        if intent in {"qualification_systeme", "obligations_entreprise", "applicability_perimetre"}:
            lines.append(
                "- La conclusion depend encore du role exact, de la qualification du systeme et du niveau de risque retenu."
            )
        else:
            lines.append("- Cette synthese ne permet pas, a elle seule, de conclure a une situation de conformite.")
        lines.append("- En cas de doute sur des decisions engageantes, une verification juridique contextualisee reste necessaire.")
        if self._is_document_request(question_text):
            doc_signals = self._document_signals(selected.core_chunks)
            if not doc_signals["high_risk"] or not doc_signals["provider_or_deployer"]:
                lines.append(
                    "- Les points documentaires cites ici ne constituent pas une checklist universelle: ils dependent de la qualification et du role."
                )
        return "\n".join(lines)

    def _is_document_request(self, question_text: str) -> bool:
        text = (question_text or "").lower()
        markers = (
            "que faut-il verifier",
            "quels documents",
            "quelles preuves",
            "quelles informations",
            "livrables",
            "que devons-nous avoir",
            "faut-il garder",
            "faut-il fournir",
        )
        return any(marker in text for marker in markers)

    def _document_signals(self, chunks: list) -> dict[str, bool]:
        text = " ".join(chunk.chunk_text.lower() for chunk in chunks)
        return {
            "high_risk": any(marker in text for marker in ("haut risque", "high-risk", "high risk")),
            "provider_or_deployer": any(
                marker in text for marker in ("fournisseur", "provider", "deployeur", "deployer")
            ),
            "transparency": any(marker in text for marker in ("transparence", "informations", "utilisateurs")),
        }

    def _role_signals(self, chunks: list) -> str:
        text = " ".join(chunk.chunk_text.lower() for chunk in chunks)
        roles: list[str] = []
        if "fournisseur" in text or "provider" in text:
            roles.append("fournisseur")
        if "deployeur" in text or "deployer" in text:
            roles.append("deployeur")
        if "importateur" in text:
            roles.append("importateur")
        return ", ".join(roles)

    def _build_document_factual_checks(self, *, selected: EvidenceSelection) -> str:
        signals = self._document_signals(selected.core_chunks)
        checks = [
            "- Documents / informations a fournir: si votre cas releve surtout de la transparence, verifier d'abord les informations a communiquer aux utilisateurs.",
            "- Preuves / traces / logs a conserver: conserver au minimum les traces permettant de justifier les informations delivrees et les controles effectues.",
            "- Elements a verifier selon votre role: confirmer si vous agissez comme fournisseur, deployeur ou autre avant de figer les obligations documentaires.",
            "- Conditions prealables avant de conclure: valider la qualification (transparence seule vs high-risk) avant d'etendre la liste des documents.",
        ]
        if signals["high_risk"]:
            checks[0] = (
                "- Documents / informations a fournir: si votre systeme releve d'un usage high-risk et selon votre role, verifier notamment documentation technique, instructions d'utilisation et informations de conformite applicables."
            )
            checks[1] = (
                "- Preuves / traces / logs a conserver: en high-risk possible, verifier la conservation des logs/traces, des elements de supervision et des preuves de controle documentaire."
            )
        if signals["high_risk"] and signals["provider_or_deployer"]:
            checks[2] = (
                "- Elements a verifier selon votre role: si vous etes provider ou deployeur sur un usage high-risk, verifier les pieces documentaires attendues pour ce role (declaration/conformite/controle selon les sources)."
            )
        if not signals["high_risk"]:
            checks[3] = (
                "- Conditions prealables avant de conclure: a ce stade, le corpus ne permet pas d'affirmer que les documents high-risk sont obligatoires pour votre cas precis."
            )
        return "\n".join(checks)

    def _classify_business_case(
        self, question_text: str
    ) -> Literal[
        "rh_recrutement",
        "service_client",
        "biometrie_surveillance_controle_acces",
        "scoring_decision_automatisee",
        "generic",
    ]:
        text = (question_text or "").lower()
        if any(
            word in text
            for word in (
                "scoring",
                "notation",
                "decision automatisee",
                "score",
            )
        ):
            return "scoring_decision_automatisee"
        if any(word in text for word in ("service client", "support client", "chatbot", "utilisateur")):
            return "service_client"
        if any(
            word in text
            for word in (
                "biometr",
                "surveillance",
                "controle d'acces",
                "controle acces",
                "reconnaissance faciale",
            )
        ):
            return "biometrie_surveillance_controle_acces"
        if any(word in text for word in ("rh", "recrutement", "candidat", "embauche", "cv", "cvs")):
            return "rh_recrutement"
        return "generic"

