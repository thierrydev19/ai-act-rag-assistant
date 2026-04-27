"""Routes HTTP backend W1."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import ApiBackendService, get_backend_service
from app.api.schemas import (
    AskRequest,
    AskResponse,
    DemoCaseResponse,
    HealthResponse,
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health(
    backend: ApiBackendService = Depends(get_backend_service),
) -> HealthResponse:
    return HealthResponse(**backend.health())


@router.get("/api/demo-cases", response_model=list[DemoCaseResponse])
def get_demo_cases(
    backend: ApiBackendService = Depends(get_backend_service),
) -> list[DemoCaseResponse]:
    return [DemoCaseResponse(**case.__dict__) for case in backend.demo_cases()]


@router.post("/api/ask", response_model=AskResponse)
def post_ask(
    payload: AskRequest,
    backend: ApiBackendService = Depends(get_backend_service),
) -> AskResponse:
    response = backend.ask(
        payload.question,
        usage_case=payload.usage_case,
        company_role=payload.company_role,
        impact_level=payload.impact_level,
    )
    return AskResponse(**response)

