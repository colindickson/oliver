# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Oliver** is a local-first productivity app built around the **3-3-3 Technique** (3 hours deep work, 3 urgent tasks, 3 maintenance tasks per day). The stack is React + TypeScript frontend, FastAPI + SQLAlchemy backend, PostgreSQL, and an MCP server exposing task data to AI agents.

## Commands

### Docker (primary workflow)

```bash
make build        # Build all Docker images
make up           # Start all services (detached)
make down         # Stop services (keep volumes)
make dev          # Start with live logs
make restart      # Restart all services
make logs         # Follow all logs
make clean        # Full reset: remove containers, networks, volumes
make reset        # clean + rebuild + start fresh
```

### Backend development

```bash
make shell-backend   # Open bash shell in backend container
make migrate         # Run Alembic migrations
make migrate-status  # Show current migration status
```

Run a single test file:
```bash
docker compose exec backend pytest tests/test_tasks.py -v
```

Run a single test:
```bash
docker compose exec backend pytest tests/test_tasks.py::test_create_task -v
```

### Frontend development

```bash
make install        # Install npm dependencies (frontend/)
make dev-frontend   # Start only frontend with logs
```

### MCP server

```bash
make mcp            # Start MCP server (stdio mode)
make mcp-build      # Build MCP server image
make install-mcp    # Register Oliver MCP in Claude Code + Claude Desktop (auto-detects path)
make uninstall-mcp  # Remove Oliver MCP from Claude Code + Claude Desktop
```

### Service URLs

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000 (docs at /api/docs)
- pgweb (DB UI): http://localhost:8081

## Architecture

### Service Boundaries

The backend API and MCP server are **independent consumers** of the same PostgreSQL database. The MCP server connects directly to Postgres (sync SQLAlchemy + psycopg2), bypassing the backend API entirely. Both have their own copy of the ORM models under their respective `models/` directories — keep them in sync when modifying the schema.

Both services share constants and validation logic via the `shared/oliver_shared/` Python package, installed via pip in both Dockerfiles. Import from `oliver_shared` (not relative paths) for task categories, statuses, and limits.

### Backend Layer Structure

```
api/        → FastAPI route handlers (HTTP boundary, request/response validation)
services/   → Business logic (stateless, injected with db session)
models/     → SQLAlchemy ORM models
schemas/    → Pydantic request/response schemas
```

Route handlers delegate to service functions; services contain all business logic. Services receive the database session as a parameter (dependency injection via FastAPI's `Depends`). The backend uses **async SQLAlchemy + asyncpg** throughout — do not introduce sync DB calls.

### Frontend Data Flow

```
pages/      → Route-level components, own TanStack Query state
components/ → Reusable UI, receive props or call hooks
hooks/      → Custom hooks for complex stateful logic (timer, reminders)
api/        → Axios client; all HTTP calls go through client.ts
```

TanStack React Query manages server state. The Vite dev server proxies `/api` to the backend container. All TypeScript types and API functions are co-located in `frontend/src/api/client.ts`.

### Data Model Core

- **Day** (one per calendar date) is the root aggregate
- **Task** belongs to a Day via `day_id`; `day_id=NULL` means a **backlog task** (also `category=NULL`)
- **Task** has `task_type`: `deep_work | short_task | maintenance` and `status`: `pending | in_progress | completed`
- Tasks have m-to-m **Tags**, 1-to-many **TimerSessions** and **Reminders**
- Days optionally have **DailyNote**, **DayRating**, **Roadblock**, **DayMetadata**, **DayOff**
- **Goal** links to tasks indirectly via shared tags; progress is computed from linked task completion
- **TaskTemplate** supports one-shot instantiation and recurring **TemplateSchedule** (weekly, bi-weekly, monthly)
- **Timer** state is in-process (not persisted while running); completed sessions are stored as **TimerSession** rows

### Testing Approach

Backend tests use **pytest-asyncio** (`asyncio_mode = auto`) with an in-memory SQLite database (via `aiosqlite`). Each test file creates its own async engine, runs `metadata.create_all`, and overrides the `get_db` FastAPI dependency with the test session. Tests hit the FastAPI app via `httpx.AsyncClient` — they are integration tests, not unit tests.

## Key Conventions

- **Alembic migrations**: Any schema change requires a new migration. Generate with `docker compose exec backend alembic revision --autogenerate -m "description"`.
- **MCP tools** live in `mcp-server/tools/` (one file per domain) and are registered as `@mcp.tool()` wrappers in `mcp-server/server.py`. Tool functions use sync SQLAlchemy sessions.
- **Frontend API calls** use the Axios instance from `src/api/client.ts` — do not use `fetch` directly.
- **Drag-and-drop** reordering uses `dnd-kit`; the backend has a dedicated `/tasks/reorder` endpoint that accepts an ordered list of task IDs.
- **Shared constants** (`CATEGORY_*`, `STATUS_*`, `MAX_TAGS_PER_TASK`) must be imported from `oliver_shared`, not redefined locally in either service.
