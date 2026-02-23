# Oliver

> "The 3-3-3 Method is a daily productivity framework designed to reduce overwhelm by structuring the workday into three distinct, manageable parts: 3 hours on a major project, 3 shorter urgent tasks, and 3 maintenance tasks. Popularized by author Oliver Burkeman, this approach promotes sustainable productivity by focusing on high-impact work and ensuring essential daily maintenance is completed without burnout."

Oliver is a local-first productivity app built around the 3-3-3 Method. It runs entirely on your machine via Docker — your data stays yours.

---

## The Method

Each day is structured into nine intentional items across three categories:

| Category | Count | Description |
|---|---|---|
| **Deep Work** | 3 hours | One major project requiring focused, uninterrupted concentration |
| **Urgent Tasks** | 3 tasks | Smaller, time-sensitive items — emails, quick reports, short meetings |
| **Maintenance** | 3 tasks | Recurring activities that keep work and life running smoothly |

---

## Features

- **Daily planning board** — a clean three-column layout for the day's nine items
- **Calendar view** — track progress across days, weeks, and months
- **Built-in timer** — stay focused during deep work sessions
- **Task management** — add, edit, delete, and reorder tasks with drag-and-drop
- **Progress tracking** — visual indicators as you complete each item
- **Analytics** — insights into how you spend your time over time
- **MCP server** — expose Oliver's task data to AI coding agents via the Model Context Protocol

---

## Architecture

```
oliver/
├── frontend/     React 18 + TypeScript + Vite + Tailwind CSS
├── backend/      FastAPI + SQLAlchemy (async) + PostgreSQL
├── mcp-server/   MCP server (stdio) for agent integration
└── docker-compose.yml
```

All services run locally via Docker Compose. Data is persisted in a named PostgreSQL volume.

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Node.js](https://nodejs.org/) (for local frontend development only)
- `make` (optional, but recommended)

### Run with Docker

```bash
# Install frontend dependencies (first time only)
make install

# Build images and start all services
make build
make up
```

The app will be available at:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000

### Common Commands

```bash
make up           # Start services (detached)
make down         # Stop and remove containers
make logs         # Tail logs from all services
make ps           # Show container status
make restart      # Restart all services
make clean        # Full reset — removes containers and volumes
make reset        # clean + rebuild + start
```

### Development Mode

```bash
make dev          # Start with live logs and auto-rebuild on changes
```

---

## MCP Server

Oliver includes an MCP (Model Context Protocol) server that allows AI agents to interact with your task data directly. It exposes tools for managing tasks, viewing the daily plan, tracking timers, and querying analytics.

### Starting the MCP Server

```bash
make mcp
```

The server runs in stdio mode and is designed to be attached to by an MCP-compatible client (e.g. Claude Desktop, Claude Code).

### Available Tool Categories

| Module | Description |
|---|---|
| `tasks` | Create, read, update, and delete tasks |
| `daily` | Fetch and manage the current day's plan |
| `timer` | Start, stop, and query work timers |
| `analytics` | Query productivity trends and summaries |

### Connecting to Claude Code

Add the following to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "oliver": {
      "command": "docker",
      "args": ["compose", "--profile", "mcp", "run", "--rm", "-i", "mcp-server"],
      "cwd": "/path/to/oliver"
    }
  }
}
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, dnd-kit |
| Backend | FastAPI, SQLAlchemy (async), Alembic, Pydantic |
| Database | PostgreSQL 16 |
| MCP Server | Python `mcp` SDK |
| Infrastructure | Docker Compose |

---

## Running Tests

```bash
make test     # Verbose output
make test-q   # Quiet output
```

Tests use `pytest` and `pytest-asyncio` against the backend application layer.

---

## License

MIT
