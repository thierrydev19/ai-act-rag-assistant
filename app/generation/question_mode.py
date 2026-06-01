"""Classification legere du mode logique des questions V2."""

from __future__ import annotations

import re

_WORD_RE = re.compile(r"\w+", re.UNICODE)

QUESTION_MODES = (
    "yes_no_non_automatic",
    "applicability_gate",
    "role_determination",
    "obligation_prioritization",
    "documents_evidence",
    "forbidden_compliance_conclusion",
    "generic_contextual",
)


def classify_question_mode(question_text: str) -> str:
    text = (question_text or "").lower()
    if any(
        marker in text
        for marker in (
            "conforme a l'ai act",
            "conforme ou non",
            "conforme oui ou non",
            "sommes-nous conformes",
            "est conforme",
        )
    ):
        return "forbidden_compliance_conclusion"
    if "automatiquement" in text or ("automatique" in text and "haut risque" in text):
        return "yes_no_non_automatic"
    if any(
        marker in text
        for marker in (
            "peut etre considere",
            "considere comme un systeme",
            "systeme a haut risque",
            "categorie sensible",
        )
    ) and ("haut risque" in text or "high-risk" in text or "?" in text):
        return "yes_no_non_automatic"
    if any(
        marker in text
        for marker in (
            "verifier en premier",
            "que faut-il verifier en premier",
            "doit verifier en premier",
        )
    ):
        return "obligation_prioritization"
    if any(
        marker in text
        for marker in (
            "nous concerne",
            "sommes-nous concernes",
            "est-ce concerne",
            "dans le perimetre",
            "champ de l'ai act",
            "entre dans le champ",
            "s'applique a nous",
        )
    ):
        return "applicability_gate"
    if any(
        marker in text
        for marker in (
            "notre role",
            "probablement notre role",
            "plutot fournisseur",
            "fournisseur, deployeur",
            "fournisseur ou deployeur",
            "simple utilisatrice",
            "notre role change",
        )
    ):
        return "role_determination"
    if "quelles obligations" in text and not any(
        word in text for word in ("transparence", "informer", "information")
    ):
        return "obligation_prioritization"
    if any(
        marker in text
        for marker in (
            "quels documents",
            "quelles preuves",
            "quelles informations",
            "livrables",
            "que devons-nous avoir",
            "faut-il garder",
            "faut-il fournir",
        )
    ):
        return "documents_evidence"
    return "generic_contextual"


def expected_answer_stance(question_mode: str) -> str:
    return {
        "yes_no_non_automatic": "non, pas automatiquement",
        "applicability_gate": "pas automatiquement / potentiellement selon le cas",
        "role_determination": "probablement / a verifier",
        "obligation_prioritization": "liste d'actions a verifier",
        "documents_evidence": "liste documentaire conditionnelle",
        "forbidden_compliance_conclusion": "refus explicite",
        "generic_contextual": "orientation generique",
    }.get(question_mode, "orientation generique")


def is_framing_question(question_text: str) -> bool:
    text = (question_text or "").lower()
    markers = (
        "sommes-nous concernes",
        "est-ce concerne",
        "est ce concerne",
        "automatiquement",
        "quel est notre role",
        "probablement notre role",
        "quelles obligations",
        "que devons-nous verifier",
        "que faut-il verifier",
        "quels documents",
        "quelles preuves",
        "quelles informations",
        "que devons-nous avoir",
        "faut-il garder",
        "faut-il fournir",
        "livrables",
    )
    return any(marker in text for marker in markers)


def should_request_business_context(question_text: str, question_mode: str) -> bool:
    if is_framing_question(question_text):
        return True
    if question_mode in {
        "yes_no_non_automatic",
        "applicability_gate",
        "role_determination",
        "obligation_prioritization",
    }:
        return True
    if question_mode == "generic_contextual" and is_framing_question(question_text):
        return True
    return False
