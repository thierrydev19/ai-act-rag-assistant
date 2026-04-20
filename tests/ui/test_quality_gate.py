"""Tests lot 10 - grille qualite MVP."""

from __future__ import annotations

import tempfile
import unittest

from app.ui.quality_gate import (
    default_quality_questions,
    format_report_markdown,
    run_quality_gate,
)
from app.ui.app import create_showcase_ui_from_chunks
from app.document.models import DocumentChunk, DocumentMetadata


def _chunk(
    *,
    chunk_index: int,
    text: str,
    page_number: int | tuple[int, int],
    article_ref: str | None = None,
) -> DocumentChunk:
    return DocumentChunk(
        metadata=DocumentMetadata(
            document_id="ai_act_fr_2024_1689_mvp",
            document_title="AI Act",
            page_number=page_number,
            article_ref=article_ref,
            section_ref=None,
            language="fr",
            version_date="2024-06-13",
            source_type="official_regulation_pdf",
            chunk_index=chunk_index,
        ),
        chunk_text=text,
    )


class TestQualityGate(unittest.TestCase):
    def test_default_question_set_has_15_items(self) -> None:
        questions = default_quality_questions()
        self.assertEqual(len(questions), 15)
        positives = [q for q in questions if q.category == "positive"]
        limits = [q for q in questions if q.category == "limit"]
        refusals = [q for q in questions if q.category == "refusal"]
        self.assertEqual(len(positives), 8)
        self.assertEqual(len(limits), 3)
        self.assertEqual(len(refusals), 4)

    def test_quality_gate_runs_and_formats_report(self) -> None:
        tmp = tempfile.mkdtemp(prefix="quality_gate_test_")
        ui = create_showcase_ui_from_chunks(
            chunks=[
                _chunk(
                    chunk_index=1,
                    text="Les obligations de transparence imposent des informations claires aux utilisateurs.",
                    page_number=52,
                    article_ref="Article 13",
                ),
                _chunk(
                    chunk_index=2,
                    text="Les sanctions administratives sont detaillees dans les dispositions finales.",
                    page_number=261,
                    article_ref="Article 99",
                ),
            ],
            collection_name="quality_gate_test",
            persist_directory=tmp,
            retrieval_max_distance=1.5,
        )
        report = run_quality_gate(ui=ui, questions=default_quality_questions()[:4])
        self.assertEqual(len(report.rows), 4)
        md = format_report_markdown(report)
        self.assertIn("Lot 10 - Grille qualite MVP", md)
        self.assertIn("| Question | Statut attendu |", md)


if __name__ == "__main__":
    unittest.main()

