"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics as analytics_router
from app.api import backlog as backlog_router
from app.api import days as days_router
from app.api import reminders as reminders_router
from app.api import tags as tags_router
from app.api import tasks as tasks_router
from app.api import timer as timer_router


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle."""
    yield


app = FastAPI(
    title="Oliver — 3-3-3 Productivity API",
    description="Local API powering the Oliver productivity application.",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(analytics_router.router)
app.include_router(backlog_router.router)
app.include_router(days_router.router)
app.include_router(reminders_router.router)
app.include_router(tags_router.router)
app.include_router(tasks_router.router)
app.include_router(timer_router.router)


@app.get("/api/health", tags=["meta"])
async def health_check() -> dict[str, str]:
    """Return a liveness probe response.

    Returns:
        A dict with ``status`` set to ``"ok"``.
    """
    return {"status": "ok"}
