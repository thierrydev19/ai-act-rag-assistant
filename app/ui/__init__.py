"""Couche interface vitrine (socle lot 1)."""

from app.ui.app import (
    DemoCase,
    ShowcaseUI,
    UiTurnView,
    build_ui,
    create_showcase_ui,
    create_showcase_ui_from_chunks,
    default_demo_cases,
)
from app.ui.quality_gate import (
    QualityEvaluationRow,
    QualityGateReport,
    QualityQuestion,
    default_quality_questions,
    format_report_markdown,
    run_quality_gate,
)

__all__ = [
    "DemoCase",
    "ShowcaseUI",
    "UiTurnView",
    "build_ui",
    "create_showcase_ui",
    "create_showcase_ui_from_chunks",
    "default_demo_cases",
    "QualityEvaluationRow",
    "QualityGateReport",
    "QualityQuestion",
    "default_quality_questions",
    "format_report_markdown",
    "run_quality_gate",
]

