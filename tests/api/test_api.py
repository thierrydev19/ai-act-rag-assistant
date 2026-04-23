"""Tests backend FastAPI lot W1."""

from __future__ import annotations

from dataclasses import dataclass
import unittest

from fastapi.testclient import TestClient

from app.api.dependencies import get_backend_service
from app.api.main import app


@dataclass(frozen=True)
class _Case:
    case_id: str
    title: str
    question: str
    expected_refusal: bool


class _FakeBackend:
    def health(self) -> dict[str, str]:
        return {"status": "ok"}

    def demo_cases(self) -> list[_Case]:
        return [
            _Case(
                case_id="transparence",
                title="Obligations de transparence",
                question="Quelles obligations de transparence ?",
                expected_refusal=False,
            )
        ]

    def ask(self, question: str) -> dict:
        if not question.strip():
            return {
                "question": question,
                "retrieval_status": "insufficient",
                "retrieval_message": "Question vide: retrieval impossible.",
                "refusal": True,
                "intent": "limites_conclusion",
                "business_case": "generic",
                "answer_simple": "Je ne peux pas conclure de maniere fiable.",
                "business_impact": ["Ne pas prendre de decision definitive."],
                "checks": ["Reformuler la question."],
                "uncertainties": ["Informations insuffisantes dans le corpus."],
                "sources": [],
                "limits": ["Pas d'avis juridique definitif."],
            }
        if "fiscal" in question.lower():
            return {
                "question": question,
                "retrieval_status": "insufficient",
                "retrieval_message": "Extraits trouves mais pertinence insuffisante.",
                "refusal": True,
                "intent": "limites_conclusion",
                "business_case": "generic",
                "answer_simple": "Je ne peux pas conclure de maniere fiable.",
                "business_impact": ["Ne pas conclure sans verification supplementaire."],
                "checks": ["Preciser le perimetre de la question."],
                "uncertainties": ["Le cas depasse le corpus charge."],
                "sources": [],
                "limits": ["Corpus insuffisant pour conclure."],
            }
        return {
            "question": question,
            "retrieval_status": "sufficient",
            "retrieval_message": "Extraits pertinents recuperes.",
            "refusal": False,
            "intent": "transparence_information",
            "business_case": "service_client",
            "answer_simple": "Des obligations de transparence existent pour certains systemes IA.",
            "business_impact": ["Preparer une information claire pour les utilisateurs."],
            "checks": ["Verifier le perimetre d'application."],
            "uncertainties": ["La qualification precise depend de votre usage."],
            "sources": ["AI Act - Article 13 - page 52"],
            "limits": ["Pas d'avis juridique definitif."],
        }


class TestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app.dependency_overrides[get_backend_service] = lambda: _FakeBackend()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        app.dependency_overrides.clear()

    def test_app_starts(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

    def test_get_health(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_get_demo_cases(self) -> None:
        response = self.client.get("/api/demo-cases")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["case_id"], "transparence")

    def test_post_ask_positive(self) -> None:
        response = self.client.post(
            "/api/ask",
            json={"question": "Quelles obligations de transparence ?"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["retrieval_status"], "sufficient")
        self.assertFalse(payload["refusal"])
        self.assertEqual(payload["business_case"], "service_client")
        self.assertGreaterEqual(len(payload["sources"]), 1)
        self.assertTrue(payload["answer_simple"])

    def test_post_ask_insufficient(self) -> None:
        response = self.client.post(
            "/api/ask",
            json={"question": "Quel regime fiscal IA mondial ?"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["retrieval_status"], "insufficient")
        self.assertTrue(payload["refusal"])
        self.assertEqual(payload["business_case"], "generic")
        self.assertEqual(payload["sources"], [])

    def test_post_ask_empty_question(self) -> None:
        response = self.client.post("/api/ask", json={"question": "   "})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["retrieval_status"], "insufficient")
        self.assertTrue(payload["refusal"])
        self.assertEqual(payload["business_case"], "generic")
        self.assertIn("Question vide", payload["retrieval_message"])

    def test_no_auth_saas_in_api_routes(self) -> None:
        from pathlib import Path
        import ast

        src = Path(__file__).resolve().parents[2] / "app" / "api" / "routes.py"
        tree = ast.parse(src.read_text(encoding="utf-8"))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        joined = "\n".join(imports).lower()
        self.assertNotIn("auth", joined)
        self.assertNotIn("saas", joined)

    def test_options_preflight_is_allowed_for_local_frontend(self) -> None:
        response = self.client.options(
            "/api/ask",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "http://localhost:3000",
        )

    def test_options_preflight_is_allowed_for_loopback_frontend(self) -> None:
        response = self.client.options(
            "/api/ask",
            headers={
                "Origin": "http://127.0.0.1:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "http://127.0.0.1:3000",
        )


if __name__ == "__main__":
    unittest.main()

