# Notification Feature Design

**Date:** 2026-03-01
**Branch:** `feature/notifications`

## Overview

An MCP-driven notification system that allows external agentic systems (e.g. `claude-cowork`) to push messages to the Oliver UI. Notifications appear as a bottom-right toast popup and in a bell icon dropdown in the sidebar.

## Goals

- Allow MCP tools to push messages to the running Oliver UI
- Show new notifications as toast popups without requiring user action
- Provide a persistent notification inbox via a bell icon in the sidebar
- Keep the system simple and standalone (no foreign keys, no user accounts)

## Non-Goals

- Real-time push (WebSockets, SSE) — polling is sufficient for this use case
- Notification categories or priority levels
- Notification persistence beyond the database (no email, no push)

---

## Data Model

### `notifications` table

| Column | Type | Constraints |
|---|---|---|
| `id` | integer | PK, autoincrement |
| `source` | varchar | NOT NULL |
| `content` | varchar(500) | NOT NULL |
| `is_read` | boolean | NOT NULL, default false, server_default false |
| `created_at` | timestamptz | NOT NULL, default UTC now |

**Design decisions:**
- Standalone table — no foreign keys to tasks, days, or users
- `content` capped at 500 characters at both the Pydantic and DB column layers
- `source` validated 1–100 characters (min_length=1, max_length=100)
- `is_read` has both a Python-side ORM default and a DB-level `server_default` for defensive insert safety

---

## API Endpoints

All routes are prefixed `/api/notifications`.

| Method | Path | Description | Status |
|---|---|---|---|
| POST | `/api/notifications` | Create a notification | 201 |
| GET | `/api/notifications` | List 5 most recent (any status) | 200 |
| GET | `/api/notifications/unread` | List all unread, newest first | 200 |
| PATCH | `/api/notifications/{id}/read` | Mark a notification as read | 200 / 404 |

**Notes:**
- `GET /notifications` accepts `?limit=N` (default 5, max 100, min 1)
- `/unread` is declared before `/{id}/read` in the router to prevent path-parameter collision (same pattern as `/reminders/due` vs `/{reminder_id}`)

---

## MCP Tool

```
notify_tool(source: str, content: str) -> str
```

- Registered in `mcp-server/server.py` as `@mcp.tool()`
- Implementation in `mcp-server/tools/notifications.py`
- Uses the sync `Notification` model in `mcp-server/models/notification.py` (mirrors backend model, uses sync SQLAlchemy + `models.base.Base`)
- Truncates `content` to 500 chars at the tool layer before inserting
- Returns `json.dumps({"id": ..., "source": ..., "content": ...})`
- Uses `get_session()` from `tools.daily` (established MCP pattern)

---

## Frontend Architecture

### Polling Strategy

| Query | Interval | Purpose |
|---|---|---|
| `GET /notifications/unread` | 15s | Drive popup display |
| `GET /notifications` | 30s | Drive bell dropdown |

### Components

**`useNotifications` hook**
- Manages both polling queries + `markRead` mutation
- Tracks `shownIds: Set<number>` in local state to suppress re-showing already-dismissed popups
- `popupNotification`: first unread not in `shownIds`
- `markPopupShown(id)`: adds to `shownIds`, does NOT mark as read in the database
- Instantiated twice (in `GlobalNotifications` and `NotificationBell`) — TanStack Query deduplicates network requests via shared cache keys; `shownIds` is intentionally local to `GlobalNotifications`

**`NotificationPopup`**
- Fixed `bottom-4 right-4 z-50`
- Blue/indigo theme — distinct from the amber `NotificationBanner` (task reminders)
- Auto-dismisses after 10 seconds using a stable `useRef` pattern to avoid timer resets on parent re-renders
- Dismiss does NOT call `markRead` — only calls `markPopupShown`
- Rendered globally in `App.tsx` via `GlobalNotifications` wrapper component

**`NotificationBell`**
- Bell SVG icon in the Sidebar header (alongside settings and theme toggle)
- Red dot badge (`aria-hidden="true"`) when `unreadCount > 0`
- `aria-label` reflects unread count for screen readers
- Toggles a dropdown showing up to 5 recent notifications (limited by the API)
- Dropdown closes on outside `mousedown`
- Each card: source (small caps, blue), content, relative time, "Mark read" button (unread only)
- Read notifications rendered at 60% opacity

### Popup vs. Mark-as-Read Separation

The popup dismissal (`markPopupShown`) is intentionally separate from the "mark read" API call. This means:
- A dismissed popup stays unread in the database
- The bell will still show the notification as unread until explicitly marked
- The popup will not re-appear for the same notification ID (tracked by `shownIds`)

This design gives the user an explicit control to acknowledge notifications rather than auto-marking them read on first display.

---

## File Inventory

| File | Action |
|---|---|
| `backend/app/models/notification.py` | Created |
| `backend/app/models/__init__.py` | Modified |
| `backend/app/schemas/notification.py` | Created |
| `backend/app/services/notification_service.py` | Created |
| `backend/app/api/notifications.py` | Created |
| `backend/app/main.py` | Modified |
| `backend/alembic/versions/b5e44acfc9a9_add_notification_model.py` | Created |
| `backend/tests/test_notifications.py` | Created |
| `mcp-server/models/notification.py` | Created |
| `mcp-server/tools/notifications.py` | Created |
| `mcp-server/server.py` | Modified |
| `frontend/src/api/client.ts` | Modified |
| `frontend/src/hooks/useNotifications.ts` | Created |
| `frontend/src/components/NotificationPopup.tsx` | Created |
| `frontend/src/components/NotificationBell.tsx` | Created |
| `frontend/src/components/Sidebar.tsx` | Modified |
| `frontend/src/App.tsx` | Modified |
| `docs/plans/2026-03-01-notifications-design.md` | Created |
