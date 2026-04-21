"""Application FastAPI W1 pour exposer le moteur MVP via HTTP."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

_DEFAULT_CORS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


def _cors_origins_from_env() -> list[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    if not raw:
        return _DEFAULT_CORS
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    return origins or _DEFAULT_CORS


app = FastAPI(
    title="AI Act RAG Assistant API",
    version="w1",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins_from_env(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(router)

