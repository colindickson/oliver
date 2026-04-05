"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sqlalchemy.exc import IntegrityError

from app.exceptions import (
    DayNotFoundError,
    GoalNotFoundError,
    InvalidOperationError,
    ScheduleNotFoundError,
    TaskNotFoundError,
    TemplateNotFoundError,
)
from app.api import analytics as analytics_router
from app.api import backlog as backlog_router
from app.api import days as days_router
from app.api import goals as goals_router
from app.api import mcp_logs as mcp_logs_router
from app.api import notifications as notifications_router
from app.api import reminders as reminders_router
from app.api import settings as settings_router
from app.api import tags as tags_router
from app.api import tasks as tasks_router
from app.api import templates as templates_router
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


@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(request: Request, exc: TaskNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(GoalNotFoundError)
async def goal_not_found_handler(request: Request, exc: GoalNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(InvalidOperationError)
async def invalid_operation_handler(request: Request, exc: InvalidOperationError) -> JSONResponse:
    return JSONResponse(status_code=exc.http_status_code, content={"detail": exc.detail})


@app.exception_handler(DayNotFoundError)
async def day_not_found_handler(request: Request, exc: DayNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(TemplateNotFoundError)
async def template_not_found_handler(request: Request, exc: TemplateNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ScheduleNotFoundError)
async def schedule_not_found_handler(request: Request, exc: ScheduleNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": "Data conflict: the operation violated a database constraint"})


app.include_router(analytics_router.router)
app.include_router(backlog_router.router)
app.include_router(days_router.router)
app.include_router(goals_router.router)
app.include_router(mcp_logs_router.router)
app.include_router(notifications_router.router)
app.include_router(reminders_router.router)
app.include_router(settings_router.router)
app.include_router(tags_router.router)
app.include_router(tasks_router.router)
app.include_router(templates_router.router)
app.include_router(timer_router.router)


@app.get("/api/health", tags=["meta"])
async def health_check() -> dict[str, str]:
    """Return a liveness probe response.

    Returns:
        A dict with ``status`` set to ``"ok"``.
    """
    return {"status": "ok"}
