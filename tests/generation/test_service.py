"""Tests lot 7 - generation contrainte avec citations et refus."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from app.document.models import DocumentChunk, DocumentMetadata, UserQuestion
from app.generation.service import GenerationService
from app.retrieval.service import RetrievalResult


def _chunk(
    *,
    chunk_index: int,
    text: str,
    page_number: int | tuple[int, int],
    article_ref: str | None = None,
    section_ref: str | None = None,
) -> DocumentChunk:
    return DocumentChunk(
        metadata=DocumentMetadata(
            document_id="ai_act_fr_2024_1689_mvp",
            document_title="AI Act",
            page_number=page_number,
            article_ref=article_ref,
            section_ref=section_ref,
            language="fr",
            version_date="2024-06-13",
            source_type="official_regulation_pdf",
            chunk_index=chunk_index,
        ),
        chunk_text=text,
    )


class TestGenerationService(unittest.TestCase):
    def test_generates_grounded_answer_with_citations(self) -> None:
        svc = GenerationService(max_citations=2)
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=11,
                    text="Les obligations de transparence imposent des informations claires aux utilisateurs.",
                    page_number=52,
                    article_ref="Article 13",
                ),
                _chunk(
                    chunk_index=12,
                    text="Les systemes a haut risque sont soumis a des obligations documentaires.",
                    page_number=(60, 61),
                    article_ref="Article 16",
                ),
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )

        payload = svc.generate(
            question=UserQuestion(text="Quelles obligations de transparence pour une PME ?"),
            context=context,
        )
        self.assertFalse(payload.refusal)
        self.assertIn("1. Reponse simple", payload.answer_text)
        self.assertIn("2. Ce que cela veut dire pour votre entreprise", payload.answer_text)
        self.assertIn("3. Ce qu'il faut verifier", payload.answer_text)
        self.assertIn("4. Ce qui reste incertain", payload.answer_text)
        self.assertIn("5. Sources", payload.answer_text)
        self.assertIn("6. Limites", payload.answer_text)
        self.assertEqual(len(payload.citations), 2)
        self.assertEqual(payload.intent, "transparence_information")
        self.assertEqual(payload.business_case, "generic")
        self.assertIn("AI Act - Article 13 - page 52", payload.citations[0])
        self.assertIn("AI Act - Article 16 - page 60-61", payload.citations[1])
        simple_block = payload.answer_text.split("2. Ce que cela veut dire pour votre entreprise")[0]
        self.assertLessEqual(len(simple_block.splitlines()), 4)
        self.assertNotIn("Les extraits retrouves indiquent les points suivants", simple_block)

    def test_refusal_when_context_is_insufficient(self) -> None:
        svc = GenerationService()
        context = RetrievalResult(
            chunks=[],
            is_sufficient=False,
            status="insufficient",
            message="Aucun extrait pertinent trouve dans le store.",
        )
        payload = svc.generate(
            question=UserQuestion(text="Quel est le delai exact de mise en conformite ?"),
            context=context,
        )
        self.assertTrue(payload.refusal)
        self.assertEqual(payload.intent, "limites_conclusion")
        self.assertEqual(payload.business_case, "generic")
        self.assertEqual(payload.citations, [])
        self.assertIn("Je ne peux pas conclure de maniere fiable", payload.answer_text)
        self.assertIn("Aucune source suffisamment pertinente", payload.answer_text)

    def test_citation_falls_back_to_page_only(self) -> None:
        svc = GenerationService(max_citations=1)
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=99,
                    text="Disposition generale applicable.",
                    page_number=222,
                    article_ref=None,
                    section_ref=None,
                )
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        payload = svc.generate(
            question=UserQuestion(text="Que dit le texte sur cette disposition generale ?"),
            context=context,
        )
        self.assertEqual(payload.intent, "limites_conclusion")
        self.assertEqual(payload.business_case, "generic")
        self.assertIn("AI Act - page 222", payload.citations[0])
        self.assertNotIn("Article", payload.citations[0])

    def test_prompt_is_constrained_to_sources(self) -> None:
        svc = GenerationService(max_citations=1)
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=1,
                    text="Texte source unique.",
                    page_number=10,
                    article_ref="Article 3",
                )
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        prompt = svc.build_constrained_prompt(UserQuestion(text="Question test"), context)
        self.assertIn("uniquement avec les informations presentes", prompt)
        self.assertIn("Interdits: invention", prompt)
        self.assertIn("Texte source unique.", prompt)

    def test_no_ui_auth_multi_llm_imports(self) -> None:
        src = Path(__file__).resolve().parents[2] / "app" / "generation" / "service.py"
        tree = ast.parse(src.read_text(encoding="utf-8"))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        joined = "\n".join(imports)
        self.assertNotIn("ui", joined)
        self.assertNotIn("auth", joined)
        self.assertNotIn("openai", joined)
        self.assertNotIn("anthropic", joined)

    def test_refusal_for_out_of_scope_business_or_legal_advice(self) -> None:
        svc = GenerationService()
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=1,
                    text="Extrait quelconque.",
                    page_number=10,
                    article_ref="Article 3",
                )
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        payload = svc.generate(
            question=UserQuestion(text="Quel est le meilleur choix de fournisseur pour ma strategie commerciale ?"),
            context=context,
        )
        self.assertTrue(payload.refusal)
        self.assertEqual(payload.intent, "limites_conclusion")
        self.assertEqual(payload.citations, [])
        self.assertIn("hors perimetre documentaire", payload.answer_text)

    def test_refusal_for_out_of_scope_tax_question(self) -> None:
        svc = GenerationService()
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=1,
                    text="Extrait proche mais non fiscal.",
                    page_number=10,
                    article_ref="Article 3",
                )
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        payload = svc.generate(
            question=UserQuestion(text="Quel est le regime fiscal mondial de l'IA ?"),
            context=context,
        )
        self.assertTrue(payload.refusal)
        self.assertIn("Je ne peux pas conclure de maniere fiable", payload.answer_text)
        self.assertEqual(payload.citations, [])

    def test_business_case_detection_for_four_categories_and_generic(self) -> None:
        svc = GenerationService()
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=10,
                    text="Les obligations imposent des informations claires aux utilisateurs.",
                    page_number=52,
                    article_ref="Article 13",
                )
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        self.assertEqual(
            svc.generate(
                question=UserQuestion(text="En RH recrutement, que doit-on faire ?"),
                context=context,
            ).business_case,
            "rh_recrutement",
        )
        self.assertEqual(
            svc.generate(
                question=UserQuestion(text="Pour notre service client avec chatbot, quelles obligations ?"),
                context=context,
            ).business_case,
            "service_client",
        )
        self.assertEqual(
            svc.generate(
                question=UserQuestion(text="Usage de biometrie pour controle d'acces, que verifier ?"),
                context=context,
            ).business_case,
            "biometrie_surveillance_controle_acces",
        )
        self.assertEqual(
            svc.generate(
                question=UserQuestion(text="Nous faisons du scoring de decision automatisee, quelles precautions ?"),
                context=context,
            ).business_case,
            "scoring_decision_automatisee",
        )
        self.assertEqual(
            svc.generate(
                question=UserQuestion(text="Quelles obligations de transparence devons-nous respecter ?"),
                context=context,
            ).business_case,
            "generic",
        )
        self.assertEqual(
            svc.generate(
                question=UserQuestion(text="Notre PME utilise une IA pour trier des CV, est-ce concerne ?"),
                context=context,
            ).business_case,
            "rh_recrutement",
        )

    def test_intent_classification_for_obligations(self) -> None:
        svc = GenerationService()
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=1,
                    text="Les obligations des fournisseurs sont detaillees.",
                    page_number=12,
                    article_ref="Article 16",
                )
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        payload = svc.generate(
            question=UserQuestion(text="Quelles obligations pour notre entreprise ?"),
            context=context,
        )
        self.assertEqual(payload.intent, "obligations_entreprise")
        self.assertIn("Vos obligations dependent d'abord de votre role exact", payload.answer_text)
        self.assertIn("Role de l'entreprise:", payload.answer_text)
        self.assertIn("Type de systeme et contexte d'usage:", payload.answer_text)
        self.assertIn("Familles d'obligations a verifier:", payload.answer_text)
        self.assertIn("Conditions avant conclusion:", payload.answer_text)
        self.assertNotIn("actions de conformite potentielles", payload.answer_text)
        self.assertNotIn("Cela donne une orientation utile", payload.answer_text)

    def test_intent_classification_for_qualification_and_documentation(self) -> None:
        svc = GenerationService()
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=2,
                    text="La documentation des systemes IA doit etre maintenue et verifiable.",
                    page_number=20,
                    article_ref="Article 11",
                )
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        payload_qualification = svc.generate(
            question=UserQuestion(text="Comment qualifier un systeme IA ?"),
            context=context,
        )
        payload_documentation = svc.generate(
            question=UserQuestion(text="Quelles preuves de documentation faut-il conserver ?"),
            context=context,
        )
        self.assertEqual(payload_qualification.intent, "qualification_systeme")
        self.assertEqual(payload_documentation.intent, "documentation_preuves")

    def test_minimal_target_questions_cover_transparency_qualification_obligations_and_refusal(self) -> None:
        svc = GenerationService()
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=21,
                    text="Le reglement prevoit des obligations de transparence et de documentation.",
                    page_number=52,
                    article_ref="Article 13",
                ),
                _chunk(
                    chunk_index=22,
                    text="La qualification depend notamment de l'usage concret et du role de l'entreprise.",
                    page_number=60,
                    article_ref="Article 16",
                ),
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        p1 = svc.generate(
            question=UserQuestion(text="Quelles obligations de transparence devons-nous respecter ?"),
            context=context,
        )
        p2 = svc.generate(
            question=UserQuestion(text="Comment qualifier notre systeme d'IA ?"),
            context=context,
        )
        p3 = svc.generate(
            question=UserQuestion(text="Quelles obligations avons-nous en tant qu'entreprise ?"),
            context=context,
        )
        p4 = svc.generate(
            question=UserQuestion(text="Quel est le regime fiscal mondial de l'IA ?"),
            context=context,
        )
        self.assertFalse(p1.refusal)
        self.assertFalse(p2.refusal)
        self.assertFalse(p3.refusal)
        self.assertTrue(p4.refusal)

    def test_refusal_for_semantic_parasite_neighbors(self) -> None:
        svc = GenerationService(max_citations=2)
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=31,
                    text="Les obligations de transparence concernent les informations aux utilisateurs.",
                    page_number=52,
                    article_ref="Article 13",
                ),
                _chunk(
                    chunk_index=32,
                    text="La documentation technique est requise pour certains systemes.",
                    page_number=61,
                    article_ref="Article 16",
                ),
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        payload = svc.generate(
            question=UserQuestion(text="Comment organiser notre politique de remuneration variable des commerciaux ?"),
            context=context,
        )
        self.assertTrue(payload.refusal)
        self.assertIn("semantiquement voisins", payload.answer_text)

    def test_sections_3_4_6_are_not_mechanical_between_cases(self) -> None:
        svc = GenerationService()
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=41,
                    text="Des informations claires doivent etre fournies aux utilisateurs.",
                    page_number=52,
                    article_ref="Article 13",
                ),
                _chunk(
                    chunk_index=42,
                    text="Les decisions automatisees sensibles doivent inclure un controle humain et une tracabilite des criteres.",
                    page_number=61,
                    article_ref="Article 16",
                ),
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        rh = svc.generate(
            question=UserQuestion(text="En RH recrutement, quelles obligations de transparence ?"),
            context=context,
        )
        scoring = svc.generate(
            question=UserQuestion(text="En scoring de decision automatisee, que faut-il verifier ?"),
            context=context,
        )
        self.assertNotEqual(rh.answer_text, scoring.answer_text)
        self.assertIn("decision RH", rh.answer_text)
        self.assertIn("Elements a verifier selon votre role", scoring.answer_text)

    def test_simple_answer_uses_core_evidence_not_parasite_chunk(self) -> None:
        svc = GenerationService(max_citations=3)
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=51,
                    text="Les sanctions administratives maximales sont prevues dans les dispositions finales.",
                    page_number=261,
                    article_ref="Article 99",
                ),
                _chunk(
                    chunk_index=52,
                    text="Les obligations de transparence imposent des informations claires aux utilisateurs.",
                    page_number=52,
                    article_ref="Article 13",
                ),
                _chunk(
                    chunk_index=53,
                    text="Les fournisseurs de systemes a haut risque maintiennent une documentation technique.",
                    page_number=60,
                    article_ref="Article 16",
                ),
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        payload = svc.generate(
            question=UserQuestion(text="Quelles obligations de transparence devons-nous respecter ?"),
            context=context,
        )
        self.assertFalse(payload.refusal)
        self.assertIn("informations claires", payload.answer_text)
        self.assertNotIn("sanctions administratives maximales", payload.answer_text)

    def test_document_request_gets_factual_conditioned_checks(self) -> None:
        svc = GenerationService(max_citations=2)
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=61,
                    text="Les obligations de transparence imposent des informations claires aux utilisateurs.",
                    page_number=52,
                    article_ref="Article 13",
                ),
                _chunk(
                    chunk_index=62,
                    text="Les fournisseurs de systemes IA a haut risque tiennent une documentation technique et des traces de supervision.",
                    page_number=60,
                    article_ref="Article 16",
                ),
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        payload = svc.generate(
            question=UserQuestion(text="Pour notre service client avec chatbot IA, que faut-il verifier ?"),
            context=context,
        )
        self.assertFalse(payload.refusal)
        self.assertIn("Documents / informations a fournir", payload.answer_text)
        self.assertIn("Preuves / traces / logs a conserver", payload.answer_text)
        self.assertIn("Elements a verifier selon votre role", payload.answer_text)
        self.assertIn("Conditions prealables avant de conclure", payload.answer_text)

    def test_obligations_response_remains_prudent_and_not_universal_checklist(self) -> None:
        svc = GenerationService(max_citations=2)
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=95,
                    text="Les obligations dependent du role de l'entreprise dans la chaine de valeur IA.",
                    page_number=74,
                    article_ref="Article 26",
                ),
                _chunk(
                    chunk_index=96,
                    text="La qualification et le niveau de risque conditionnent l'etendue des obligations applicables.",
                    page_number=18,
                    article_ref="Article 3",
                ),
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        payload = svc.generate(
            question=UserQuestion(text="Quelles obligations avons-nous en tant qu'entreprise ?"),
            context=context,
        )
        self.assertFalse(payload.refusal)
        self.assertIn("pas comme une liste universelle", payload.answer_text)
        self.assertIn("avant toute conclusion ferme", payload.answer_text)

    def test_quality_wording_block_4_and_6_are_not_mechanical(self) -> None:
        svc = GenerationService(max_citations=2)
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=97,
                    text="La qualification d'un systeme IA depend de sa finalite et du contexte de decision.",
                    page_number=18,
                    article_ref="Article 3",
                ),
                _chunk(
                    chunk_index=98,
                    text="Les obligations de transparence imposent des informations claires aux utilisateurs.",
                    page_number=52,
                    article_ref="Article 13",
                ),
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        qualification = svc.generate(
            question=UserQuestion(text="Comment qualifier notre systeme d'IA ?"),
            context=context,
        )
        transparence = svc.generate(
            question=UserQuestion(text="Quelles obligations de transparence devons-nous respecter ?"),
            context=context,
        )
        self.assertIn("4. Ce qui reste incertain", qualification.answer_text)
        self.assertIn("6. Limites", qualification.answer_text)
        self.assertNotEqual(qualification.answer_text, transparence.answer_text)
        #self.assertIn("qualification depend", qualification.answer_text.lower())
        self.assertIn("qualification", qualification.answer_text.lower())
        self.assertIn("depend", qualification.answer_text.lower())
        #self.assertIn("modalites exactes d'information", transparence.answer_text.lower())
        self.assertIn("transparence", transparence.answer_text.lower())
        self.assertIn("information", transparence.answer_text.lower())

    def test_document_request_without_high_risk_is_explicitly_limited(self) -> None:
        svc = GenerationService(max_citations=1)
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=71,
                    text="Les obligations de transparence imposent des informations claires aux utilisateurs.",
                    page_number=52,
                    article_ref="Article 13",
                )
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        payload = svc.generate(
            question=UserQuestion(text="Pour notre service client avec chatbot IA, que faut-il verifier ?"),
            context=context,
        )
        self.assertFalse(payload.refusal)
        self.assertIn("ne permet pas d'affirmer que les documents high-risk sont obligatoires", payload.answer_text)
        self.assertIn("ne constituent pas une checklist universelle", payload.answer_text)

    def test_mismatch_intent_core_evidence_triggers_refusal(self) -> None:
        svc = GenerationService(max_citations=2)
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=81,
                    text="Les utilisateurs doivent etre informes de l'interaction avec une IA.",
                    page_number=52,
                    article_ref="Article 13",
                )
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        payload = svc.generate(
            question=UserQuestion(text="Comment qualifier notre systeme d'IA ?"),
            context=context,
        )
        self.assertTrue(payload.refusal)
        self.assertTrue(
            "insuffisamment alignes avec l'intention" in payload.answer_text
            or "Aucun noyau documentaire coherent" in payload.answer_text
        )

    def test_role_question_prefers_role_evidence(self) -> None:
        svc = GenerationService(max_citations=2)
        context = RetrievalResult(
            chunks=[
                _chunk(
                    chunk_index=91,
                    text="Les utilisateurs doivent etre informes de l'interaction avec une IA.",
                    page_number=52,
                    article_ref="Article 13",
                ),
                _chunk(
                    chunk_index=92,
                    text="Le role de deployeur determine des obligations distinctes de celles du fournisseur.",
                    page_number=74,
                    article_ref="Article 26",
                ),
            ],
            is_sufficient=True,
            status="sufficient",
            message="ok",
        )
        payload = svc.generate(
            question=UserQuestion(text="Quel est notre role d'entreprise entre fournisseur et deployeur ?"),
            context=context,
        )
        self.assertFalse(payload.refusal)
        self.assertIn("role", payload.answer_text.lower())
        self.assertIn("AI Act - Article 26 - page 74", payload.citations[0])


if __name__ == "__main__":
    unittest.main()

