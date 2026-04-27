"""Tests de lisibilite UI web pour les 6 blocs V2."""

from __future__ import annotations

import unittest
from pathlib import Path


class TestWebRendering(unittest.TestCase):
    def setUp(self) -> None:
        page = Path(__file__).resolve().parents[2] / "web" / "src" / "app" / "page.tsx"
        self.source = page.read_text(encoding="utf-8")

    def test_ui_keeps_all_six_blocks_visible(self) -> None:
        self.assertIn('title="Reponse simple"', self.source)
        self.assertIn('title="Ce que cela veut dire pour votre entreprise"', self.source)
        self.assertIn('title="Ce qu\'il faut verifier"', self.source)
        self.assertIn('title="Ce qui reste incertain"', self.source)
        self.assertIn('title="Sources"', self.source)
        self.assertIn('title="Limites"', self.source)

    def test_result_blocks_use_visual_separation(self) -> None:
        self.assertIn("rounded-xl border border-zinc-200 bg-white p-5 shadow-sm", self.source)
        self.assertIn("space-y-6 md:space-y-7", self.source)
        self.assertIn("space-y-4", self.source)

    def test_items_are_rendered_line_by_line(self) -> None:
        self.assertIn('item.split("\\n").map', self.source)
        self.assertIn("whitespace-pre-wrap", self.source)
        self.assertIn("border-b border-zinc-100 pb-2", self.source)
        self.assertIn("leading-7", self.source)

    def test_refusal_stays_explicitly_visible(self) -> None:
        self.assertIn("refus explicite", self.source)
        self.assertIn("bg-rose-100", self.source)

    def test_context_collection_ui_is_lightweight_and_conditional(self) -> None:
        self.assertIn("result?.context_needed", self.source)
        self.assertIn("Precisions recommandees (optionnelles)", self.source)
        self.assertIn("cas d&apos;usage: je ne sais pas", self.source)
        self.assertIn("role: je ne sais pas", self.source)
        self.assertIn("impact: je ne sais pas", self.source)


if __name__ == "__main__":
    unittest.main()

