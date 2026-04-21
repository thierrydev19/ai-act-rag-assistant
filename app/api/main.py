"""Application FastAPI W1 pour exposer le moteur MVP via HTTP."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="AI Act RAG Assistant API",
    version="w1",
)
app.include_router(router)

