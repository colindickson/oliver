# Oliver

> "The 3-3-3 Technique is a daily productivity framework designed to reduce overwhelm by structuring the workday into three distinct, manageable parts: 3 hours on a major project, 3 shorter urgent tasks, and 3 maintenance tasks. Popularized by author Oliver Burkeman, this approach promotes sustainable productivity by focusing on high-impact work and ensuring essential daily maintenance is completed without burnout."

Oliver is a local-first productivity app built around the 3-3-3 Technique. It runs entirely on your machine via Docker — your data stays yours.

---

## The Method

Each day is structured into intentional items across three categories:

| Category | Count | Description |
|---|---|---|
| **Deep Work** | 3 hours | One major project requiring focused, uninterrupted concentration |
| **Urgent Tasks** | 3 tasks | Smaller, time-sensitive items — emails, quick reports, short meetings |
| **Maintenance** | 3 tasks | Recurring activities that keep work and life running smoothly |

---

## Features

- **Daily planning board** — three-column layout (deep work, urgent tasks, maintenance) for the day
- **Backlog** — unscheduled task queue with full-text search and tag filtering
- **Goals** — long-term objectives with linked tasks and progress tracking
- **Calendar view** — navigate and edit any past or future day
- **Tags** — tag-based task organization with browsable tag pages
- **Built-in timer** — start, pause, and stop timers during deep work sessions
- **Task management** — add, edit, delete, reorder (drag-and-drop), and move tasks between days
- **Day reflections** — daily notes, roadblocks, and energy ratings per day
- **Progress tracking** — visual completion rings and per-category stats
- **Analytics** — completion trends, streaks, and category breakdowns over time
- **MCP server** — expose Oliver's task data to AI coding agents via the Model Context Protocol

---

## Architecture

```
oliver/
├── frontend/     React 18 + TypeScript + Vite + Tailwind CSS
├── backend/      FastAPI + SQLAlchemy (async) + PostgreSQL
├── mcp-server/   MCP server (stdio) for agent integration
├── shared/       Shared Python library (constants, validation)
└── docker-compose.yml
```

All services run locally via Docker Compose. Data is persisted in a named PostgreSQL volume.

The `shared/` package contains common Python code used by both the backend and MCP server.

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

### Connecting to Claude Code or Claude Desktop

The MCP server uses stdio transport. The **main services (postgres) must be running** before connecting:

```bash
make up
```

#### Claude Code

Add the server via the CLI:

```bash
claude mcp add oliver -- docker compose -f /path/to/oliver/docker-compose.yml run --rm -i -T mcp-server
```

Or manually add the following to `~/.claude.json` under `mcpServers`:

```json
{
  "mcpServers": {
    "oliver": {
      "command": "docker",
      "args": [
        "compose",
        "-f", "/path/to/oliver/docker-compose.yml",
        "run", "--rm", "-i", "-T",
        "mcp-server"
      ]
    }
  }
}
```

> **Note on `-f` and `cwd`:** The `-f` flag points `docker compose` at the project's `docker-compose.yml` using an absolute path, so the command works from any working directory. `cwd` sets the working directory for `docker compose` on the host — it should be the Oliver project root. Neither is a path inside the container.

> **Note on `-T`:** The `-T` flag disables pseudo-TTY allocation. This is required for stdio-based MCP transport, which communicates over raw stdin/stdout.

#### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) and add the same block under `mcpServers`:

```json
{
  "mcpServers": {
    "oliver": {
      "command": "docker",
      "args": [
        "compose",
        "-f", "/path/to/oliver/docker-compose.yml",
        "run", "--rm", "-i", "-T",
        "mcp-server"
      ]
    }
  }
}
```

Restart Claude Desktop after saving. On Windows the config file is at `%APPDATA%\Claude\claude_desktop_config.json`.

#### Verify the connection

Once configured, ask Claude: _"What's on my Oliver plan for today?"_ — it should call `get_daily_plan_tool` and return your tasks.

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

## Contributing

Contributions are welcome! Please open an issue or submit a pull request with improvements, bug fixes, or new features. For major changes, please discuss them in an issue first.

### TODOs

* Improve UI/UX design
* Add user authentication and multi-user support
* Implement Github / Linear / Jira integrations
* Add support for recurring tasks and templates
* Enhance analytics with more detailed reports and visualizations


---

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE) or later.
