# Day Overview Modal and JSON Export

## Overview

Add a modal that appears when clicking a calendar day, showing a summary and expandable task list. Add JSON export functionality for day/week/custom date ranges, accessible from both the modal and calendar header.

## Requirements

- Day click opens modal (instead of just navigating to /day/{date})
- Modal shows task summary with expandable full list
- Export to JSON for day, week, or custom date range
- Export accessible from both day modal and calendar header

## Component Architecture

### New Components
```
frontend/src/components/
├── DayOverviewModal.tsx    # Modal shown on calendar day click
├── ExportModal.tsx         # Modal for export with date range selection
└── TaskListExpandable.tsx  # Reusable expandable task list
```

### Modified Components
- **Calendar.tsx** - Add onDayClick handler for DayOverviewModal, add Export button to header
- **api/client.ts** - Add exportTasks(dateFrom, dateTo) function

### State Management
- Modal open/close state lives in Calendar.tsx (parent)
- Selected date passed to DayOverviewModal as prop
- ExportModal manages its own date range state

## DayOverviewModal

### Layout
```
┌─────────────────────────────────────────────┐
│  ☀  February 22, 2026                    ✕  │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  SUMMARY CARD                        │   │
│  │  8 tasks total • 5 completed (63%)   │   │
│  │  ────────────────────────────────    │   │
│  │  Deep Work:    3/4 tasks             │   │
│  │  Short Tasks:  2/3 tasks             │   │
│  │  Maintenance:  0/1 tasks             │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  [▼ Show all tasks]                         │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ EXPANDED TASK LIST (when expanded)   │   │
│  │  - Grouped by category               │   │
│  │  - Shows status (checkmark/circle)   │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  [Export this day]  [View full page →]      │
│                                             │
└─────────────────────────────────────────────┘
```

### Behavior
- Summary card shows counts by category with completion progress
- Expand/collapse toggle shows full task list grouped by category
- Export button triggers JSON download for that single day
- View full page link navigates to /day/{date}

## ExportModal

### Layout
```
┌─────────────────────────────────────────────┐
│  ↓ Export Tasks                          ✕  │
├─────────────────────────────────────────────┤
│                                             │
│  Export period                              │
│  ○ Day  ○ Week  ● Custom range             │
│                                             │
│  Custom range (when selected)               │
│  From:  [Feb 15, 2026    📅]               │
│  To:    [Feb 22, 2026    📅]               │
│                                             │
│  Preview                                    │
│  Feb 15-22, 2026 • 47 tasks • 68% complete  │
│                                             │
│  [Cancel]              [Download JSON]      │
└─────────────────────────────────────────────┘
```

### Behavior
- Period selector: Radio buttons for Day/Week/Custom
- Day mode: Uses passed date (from DayOverviewModal) or today
- Week mode: Auto-calculates Mon-Sun for selected date
- Custom mode: Shows date pickers for from/to
- Preview shows task count and completion stats
- Download triggers browser JSON file download

### File Naming
```
tasks-export-2026-02-22.json
tasks-export-2026-02-16-to-2026-02-22.json
```

## JSON Export Structure

```json
{
  "export_metadata": {
    "exported_at": "2026-02-22T14:30:00Z",
    "period": {
      "type": "custom_range",
      "from": "2026-02-15",
      "to": "2026-02-22"
    }
  },
  "summary": {
    "total_tasks": 47,
    "completed": 32,
    "completion_rate": 0.68,
    "by_category": {
      "deep_work": { "total": 15, "completed": 12 },
      "short_task": { "total": 25, "completed": 16 },
      "maintenance": { "total": 7, "completed": 4 }
    }
  },
  "days": [
    {
      "date": "2026-02-15",
      "day_id": 142,
      "total_tasks": 6,
      "completed": 4,
      "completion_rate": 0.67,
      "tasks": [
        {
          "id": 1023,
          "title": "Review quarterly report",
          "description": "Go through Q4 metrics",
          "category": "deep_work",
          "status": "completed",
          "completed_at": "2026-02-15T11:30:00Z",
          "order_index": 0,
          "timer_sessions": [
            { "started_at": "2026-02-15T09:00:00Z", "duration_seconds": 1800 }
          ]
        }
      ]
    }
  ]
}
```

## Technical Notes

- Use existing ReminderDialog.tsx modal pattern for consistency
- Reuse existing API client patterns for data fetching
- Export will fetch data via API and construct JSON client-side
- Browser download using Blob and URL.createObjectURL
