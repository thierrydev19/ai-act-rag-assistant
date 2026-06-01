"""Tests intent + question_mode + evidence selection."""

from __future__ import annotations

import unittest

from app.document.models import DocumentChunk, DocumentMetadata
from app.generation.evidence_selection import EvidenceSelector


def _chunk(*, idx: int, text: str, article: str | None = None) -> DocumentChunk:
    return DocumentChunk(
        metadata=DocumentMetadata(
            document_id="ai_act_fr_2024_1689_mvp",
            document_title="AI Act",
            page_number=52,
            article_ref=article,
            section_ref=None,
            language="fr",
            version_date="2024-06-13",
            source_type="official_regulation_pdf",
            chunk_index=idx,
        ),
        chunk_text=text,
    )


class TestQuestionModeEvidence(unittest.TestCase):
    def test_q6_supervision_not_preferred_over_qualification(self) -> None:
        selector = EvidenceSelector(max_core=2)
        question = (
            "Nous avons un chatbot sur notre site web qui repond aux questions clients. "
            "Est-ce automatiquement un systeme a haut risque ?"
        )
        qualification = _chunk(
            idx=1,
            article="Article 3",
            text="La qualification d'un systeme IA depend de sa finalite, de son usage et des categories annexe.",
        )
        supervision = _chunk(
            idx=2,
            article="Article 14",
            text="La supervision humaine effective est exigee pour les systemes a haut risque.",
        )
        selected = selector.select(
            question_text=question,
            chunks=[supervision, qualification],
            intent="qualification_systeme",
            question_mode="yes_no_non_automatic",
        )
        self.assertTrue(selected.mode_aligned)
        self.assertEqual(selected.core_chunks[0], qualification)

    def test_q1_detailed_obligations_not_core_for_applicability(self) -> None:
        selector = EvidenceSelector(max_core=1, min_score=0.05)
        question = (
            "Nous sommes une PME qui utilise ChatGPT pour rediger des emails internes. "
            "Est-ce que l'AI Act nous concerne ?"
        )
        applicability = _chunk(
            idx=1,
            article="Article 2",
            text="Le champ d'application et les exclusions definissent quels systemes sont concernes.",
        )
        obligations = _chunk(
            idx=2,
            article="Article 16",
            text="Les obligations detaillees de documentation technique s'appliquent aux fournisseurs.",
        )
        selected = selector.select(
            question_text=question,
            chunks=[obligations, applicability],
            intent="applicability_perimetre",
            question_mode="applicability_gate",
        )
        self.assertTrue(selected.mode_aligned)
        self.assertEqual(selected.core_chunks[0], applicability)


if __name__ == "__main__":
    unittest.main()
