"""Schemas HTTP pour le backend web W1."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class DemoCaseResponse(BaseModel):
    case_id: str
    title: str
    question: str
    expected_refusal: bool


class AskRequest(BaseModel):
    question: str = Field(default="", description="Question utilisateur brute")
    usage_case: str | None = Field(default=None, description="Cas d'usage principal")
    company_role: str | None = Field(default=None, description="Role principal de l'entreprise")
    impact_level: str | None = Field(default=None, description="Niveau d'impact du systeme")


class AskResponse(BaseModel):
    question: str
    retrieval_status: str
    retrieval_message: str
    refusal: bool
    intent: str
    business_case: str
    answer_simple: str
    business_impact: list[str]
    checks: list[str]
    uncertainties: list[str]
    sources: list[str]
    limits: list[str]
    context_needed: bool = False
    context_questions: list[str] = Field(default_factory=list)
    context_used: dict[str, str] = Field(default_factory=dict)

