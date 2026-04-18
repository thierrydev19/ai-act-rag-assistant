"""Vérifications de structure du lot 1."""

from pathlib import Path
import unittest

from app.main import bootstrap


class TestProjectStructure(unittest.TestCase):
    """Tests structurels du socle MVP."""

    def test_required_directories_exist(self) -> None:
        """Valide la présence des blocs d'architecture MVP."""
        expected_dirs = [
            "app/ingestion",
            "app/document",
            "app/chunking",
            "app/embeddings",
            "app/retrieval",
            "app/generation",
            "app/ui",
            "app/logging",
            "tests",
        ]

        for relative_dir in expected_dirs:
            with self.subTest(relative_dir=relative_dir):
                self.assertTrue(Path(relative_dir).is_dir(), f"Missing directory: {relative_dir}")

    def test_bootstrap_import_and_state(self) -> None:
        """Vérifie que les imports de base ne cassent pas le projet."""
        state = bootstrap()
        self.assertEqual(state.ingestion, "ready")
        self.assertEqual(state.retrieval, "ready")
        self.assertEqual(state.generation, "ready")


if __name__ == "__main__":
    unittest.main()

