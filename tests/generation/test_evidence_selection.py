"""Tests lot 3 V2 - evidence selection."""

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


class TestEvidenceSelection(unittest.TestCase):
    def test_parasite_chunk_is_not_core_when_off_topic(self) -> None:
        selector = EvidenceSelector(max_core=2)
        question = "Pour notre service client avec chatbot IA, que faut-il verifier ?"
        core = _chunk(
            idx=1,
            article="Article 13",
            text="Les obligations de transparence imposent des informations claires aux utilisateurs.",
        )
        parasite = _chunk(
            idx=2,
            article="Article 99",
            text="Les sanctions administratives et amendes globales sont detaillees dans les dispositions finales.",
        )
        selected = selector.select(question_text=question, chunks=[parasite, core])
        self.assertTrue(selected.core_chunks)
        self.assertIn(core, selected.core_chunks)
        self.assertNotIn(parasite, selected.core_chunks[:1])

    def test_core_evidence_is_limited_to_two_chunks(self) -> None:
        selector = EvidenceSelector(max_core=2)
        question = "Quelles obligations de transparence devons-nous respecter ?"
        selected = selector.select(
            question_text=question,
            chunks=[
                _chunk(idx=1, article="Article 13", text="Transparence et informations utilisateurs."),
                _chunk(idx=2, article="Article 16", text="Documentation pour systemes a haut risque."),
                _chunk(idx=3, article="Article 52", text="Marquage CE et obligations annexes."),
            ],
        )
        self.assertLessEqual(len(selected.core_chunks), 2)

    def test_dispersed_chunks_can_be_marked_incoherent(self) -> None:
        selector = EvidenceSelector(max_core=2, min_score=0.2)
        question = "Comment qualifier notre systeme d'IA ?"
        selected = selector.select(
            question_text=question,
            chunks=[
                _chunk(idx=1, text="Cadre des sanctions administratives."),
                _chunk(idx=2, text="Regles budgetaires generales d'un Etat membre."),
            ],
        )
        self.assertFalse(selected.is_coherent)
        self.assertFalse(selected.core_chunks)

    def test_qualification_prefers_qualification_over_transparency(self) -> None:
        selector = EvidenceSelector(max_core=2)
        question = "Comment qualifier notre systeme d'IA ?"
        transparency = _chunk(
            idx=10,
            article="Article 13",
            text="Les utilisateurs doivent etre informes de l'interaction avec une IA.",
        )
        qualification = _chunk(
            idx=11,
            article="Article 3",
            text="La qualification d'un systeme IA depend de sa finalite d'usage et de son contexte.",
        )
        selected = selector.select(
            question_text=question,
            chunks=[transparency, qualification],
            intent="qualification_systeme",
        )
        self.assertTrue(selected.intent_aligned)
        self.assertEqual(selected.core_chunks[0], qualification)

    def test_transparency_prefers_transparency_over_high_risk_documentation(self) -> None:
        selector = EvidenceSelector(max_core=2)
        question = "Quelles obligations de transparence devons-nous respecter ?"
        transparency = _chunk(
            idx=20,
            article="Article 13",
            text="Les obligations de transparence imposent des informations claires aux utilisateurs.",
        )
        high_risk = _chunk(
            idx=21,
            article="Article 16",
            text="Le fournisseur conserve la documentation technique et les procedures qualite pour le high-risk.",
        )
        selected = selector.select(
            question_text=question,
            chunks=[high_risk, transparency],
            intent="transparence_information",
        )
        self.assertTrue(selected.intent_aligned)
        self.assertEqual(selected.core_chunks[0], transparency)

    def test_intent_mismatch_detected_for_wrong_core_family(self) -> None:
        selector = EvidenceSelector(max_core=2)
        question = "Comment qualifier notre systeme d'IA ?"
        transparency_only = _chunk(
            idx=30,
            article="Article 13",
            text="L'utilisateur doit etre informe de l'interaction avec un systeme IA.",
        )
        selected = selector.select(
            question_text=question,
            chunks=[transparency_only],
            intent="qualification_systeme",
        )
        self.assertFalse(selected.intent_aligned)
        self.assertIn("intention", selected.message)


if __name__ == "__main__":
    unittest.main()

