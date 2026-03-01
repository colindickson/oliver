# Oliver

A local-first productivity app built around Oliver Burkeman's 3-3-3 Technique.

---

## The 3-3-3 Technique

> "The 3-3-3 Technique is a daily productivity framework designed to reduce overwhelm by structuring the workday into three distinct, manageable parts: 3 hours on a major project, 3 shorter urgent tasks, and 3 maintenance tasks. Popularized by author Oliver Burkeman, this approach promotes sustainable productivity by focusing on high-impact work and ensuring essential daily maintenance is completed without burnout."

Popularized by Oliver Burkeman — author of the book *Four Thousand Weeks* — the 3-3-3 Technique structures each workday into three intentional parts. The goal is sustainable focus without overwhelm — not more output, but clearer priorities.

| Category | Amount | Description |
|---|---|---|
| **Deep Work** | 3 hours | One major project requiring focused, uninterrupted concentration |
| **Urgent Tasks** | 3 tasks | Smaller, time-sensitive items — emails, quick reports, short meetings |
| **Maintenance** | 3 tasks | Recurring upkeep that keeps work and life running smoothly |

---

## Motivation

As a software developer, attention is my primary resource. Many roles come with more context switches than I can comfortably absorb — emails, Jira updates, meetings, code reviews, reports, evaluations. Each switch has a cost, and without deliberate structure, the day fragments before meaningful work can begin.

I needed structure, but too much structure — spread across different tools — becomes its own source of overhead and resistance.

The 3-3-3 technique operates at exactly the right level for me. It's flexible enough to let me define and organize my own tasks each day, simple enough that maintaining it doesn't become a job in itself, and clear enough that I always know what I've committed to and what I've done.

The included MCP server also makes it easy to integrate Oliver into modern agentic workflows — letting me use Claude to connect tasks across different systems in whatever way fits the moment.

I believe that this tool can help others in knowledge work roles — developers, writers, researchers — who face similar challenges of attention fragmentation and want a simple, local-first way to apply the 3-3-3 method.

---

## Who This Is For

Oliver is useful for knowledge workers — developers, writers, researchers — who want to apply the 3-3-3 method with a clean local app and keep their data on their own machine. It also ships with an MCP server, making it a practical task planning layer for AI coding agents like Claude Code and Claude Desktop.

---

## Requirements

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- `make`
- `python 3.12+`

---

## Getting Started

```bash
make start
```

Open the app in your browser at http://localhost:5173

---

## MCP Integration

Oliver includes an MCP server that exposes task data to AI agents over stdio. The main services must be running (`make start`) before connecting.

### Installation

Run the following command from the Oliver directory to automatically install the MCP server for both Claude Code and Claude Desktop:

```bash
make install-mcp
```

Or install for each client individually:

```bash
make install-mcp-claude-code     # Claude Code only
make install-mcp-claude-desktop  # Claude Desktop only
```

The correct path is detected automatically — no manual config editing required.

### Available MCP Tools

| Tool | Description |
|---|---|
| `get_daily_plan` | Get all tasks for a given date (defaults to today) |
| `set_daily_plan` | Replace the full task list for a date with a new set of tasks |
| `create_task` | Create a single task with a title, category (`deep_work`, `short_task`, `maintenance`), optional description, and tags |
| `update_task` | Update a task's title, description, status, or tags by ID |
| `complete_task` | Mark a task as completed by ID |
| `delete_task` | Delete a task by ID |
| `start_timer` | Start the timer for a task (resumes if previously paused) |
| `stop_timer` | Stop the running timer and record the session |
| `get_analytics` | Get productivity analytics for the past N days |
| `mark_day_off` | Mark a day as off with a reason (`sick_day`, `vacation`, `holiday`, `personal_day`, `weekend`) and optional note |
| `unmark_day_off` | Remove the off-day designation for a date |
| `list_days_off` | List all days marked as off, newest first |
| `get_recurring_days_off` | Get the configured recurring off weekdays (e.g. Saturday, Sunday) |
| `set_recurring_days_off` | Set which weekdays are always treated as off days |
| `set_day_metadata` | Record weather condition, temperature, and moon phase for a day |

### Example: Planning your day with Claude

Once Oliver is connected as an MCP server, you can talk to Claude naturally:

> "Plan my day — I have a PR review that needs to happen before standup, I want to spend the morning on the auth refactor, and I need to update the team wiki."

Claude will create the appropriate tasks across the three 3-3-3 categories. You can also ask things like:

- *"What did I get done this week?"* → uses `get_analytics`
- *"I'm sick, mark tomorrow as a sick day"* → uses `mark_day_off`
- *"Start the timer on my deep work task"* → uses `start_timer`

---

## Contributing

Contributions are welcome — bugs, features, and improvements. Open an issue before starting major changes. Fork the repo, work on a feature branch, and submit a PR. Keep commits concise and in imperative mood.

---

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE) or later.
