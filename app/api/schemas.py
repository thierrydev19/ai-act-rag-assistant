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


class AskResponse(BaseModel):
    question: str
    retrieval_status: str
    retrieval_message: str
    refusal: bool
    intent: str
    answer_simple: str
    business_impact: list[str]
    checks: list[str]
    uncertainties: list[str]
    sources: list[str]
    limits: list[str]

