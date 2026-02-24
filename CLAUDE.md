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
```

### Service URLs

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- pgweb (DB UI): http://localhost:8081

## Architecture

### Service Boundaries

The backend API and MCP server are **independent consumers** of the same PostgreSQL database. The MCP server connects directly to Postgres (sync SQLAlchemy + psycopg2), bypassing the backend API entirely. Both have their own copy of the ORM models under their respective `models/` directories — keep them in sync when modifying the schema.

### Backend Layer Structure

```
api/        → FastAPI route handlers (HTTP boundary, request/response validation)
services/   → Business logic (stateless, injected with db session)
models/     → SQLAlchemy ORM models
schemas/    → Pydantic request/response schemas
```

Route handlers delegate to service functions; services contain all business logic. Services receive the database session as a parameter (dependency injection via FastAPI's `Depends`).

### Frontend Data Flow

```
pages/      → Route-level components, own TanStack Query state
components/ → Reusable UI, receive props or call hooks
hooks/      → Custom hooks for complex stateful logic (timer, reminders)
api/        → Axios client; all HTTP calls go through client.ts
```

TanStack React Query manages server state. The Vite dev server proxies `/api` to the backend container.

### Data Model Core

- **Day** (one per calendar date) is the root aggregate
- **Task** belongs to a Day and has a `task_type` enum: `deep_work | short_task | maintenance`
- **Task** has `status`: `pending | in_progress | completed`
- Tasks have m-to-m **Tags**, 1-to-many **TimerSessions**, **Reminders**
- Days optionally have **DailyNote**, **DayRating**, **Roadblock**

### Testing Approach

Backend tests use **pytest-asyncio** with an in-memory SQLite database (via `aiosqlite`). The `conftest.py` sets up an async engine, creates all tables, and provides a session fixture per test. Tests hit the FastAPI app via `httpx.AsyncClient` — they are integration tests, not unit tests.

## Key Conventions

- **Alembic migrations**: Any schema change requires a new migration. Generate with `docker compose exec backend alembic revision --autogenerate -m "description"`.
- **Async backend**: All database operations use `async/await` with `asyncpg`. Do not introduce sync DB calls in the backend.
- **MCP tools** live in `mcp-server/tools/` and are registered in `mcp-server/server.py`. Tool functions use sync SQLAlchemy sessions.
- **Frontend API calls** use the Axios instance from `src/api/client.ts` — do not use `fetch` directly.
- **Drag-and-drop** reordering uses `dnd-kit`; the backend has a dedicated `/reorder` endpoint that accepts an ordered list of task IDs.
