# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

Oliver is a 5-service Docker Compose monorepo: `backend` (FastAPI/Python 3.12 async), `frontend` (React 18/TypeScript), `mcp-server`, `postgres` (PostgreSQL 16), and `shared` (Python package).

## Development Workflow

Everything runs in Docker — never run services outside containers.

| Command | Purpose |
|---------|---------|
| `make start` | Build + start all services |
| `make up` | Start without rebuilding |
| `make down` | Stop (keeps data volumes) |
| `make logs` | Follow all service logs |
| `make shell-backend` | Bash in backend container |
| `make shell-database` | psql in postgres |

## Testing

```bash
make test       # pytest in backend container
cd frontend && npm test  # vitest (frontend)
```

Backend tests use **in-memory SQLite** — not PostgreSQL. PostgreSQL-specific behavior won't be covered.

Frontend tests live in `frontend/src/` alongside components (`*.test.tsx`). The setup file at `src/test-setup.ts` imports `@testing-library/jest-dom` matchers globally.

## Database Migrations

```bash
make migrate        # Auto-generate + apply new migration (use when adding/modifying models)
make upgrade-db     # Apply pending migrations only
make migrate-status # Show migration state
```

Use `make migrate` when you add or change a SQLAlchemy model. Use `make upgrade-db` only to apply pre-existing scripts.

## Architecture Constraints

- **Async-first**: All DB operations must use `async/await` (asyncpg + SQLAlchemy 2.0). No sync DB calls.
- **Service layer**: Business logic belongs in `app/services/`, not in route handlers (`app/api/`).
- **Pydantic v2**: All schemas use Pydantic 2 syntax.
- **Shared package**: Changes to `shared/` require rebuilding backend + mcp-server (`make build`).

## Linting

```bash
# Python (backend + mcp-server) — install ruff separately: pip install ruff
ruff check backend/ mcp-server/
ruff format backend/ mcp-server/

# TypeScript (frontend) — run after: cd frontend && npm install
npm run lint
```

## Commits

Push directly to `main`. No feature branches or PRs unless asked.
