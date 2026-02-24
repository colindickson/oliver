# Task Inline Editing on DayDetail Page

## Summary

Add inline editing capability for tasks on the DayDetail page (`/day/{date}`), allowing users to edit title, description, and tags for past, present, and future tasks.

## Current State

- **TaskCard.tsx** (used on Today page) has inline editing for title, description, and tags
- **DayDetail.tsx** only supports toggling completion status and deleting tasks

## Design

### Approach

Extract the inline editing logic into a reusable `useTaskEdit` hook, then apply it to DayDetail tasks.

### Changes

1. Create `useTaskEdit` hook with:
   - Edit state (editing, editTitle, editDescription, editTags, saving)
   - `openEdit()` function to initialize state from task
   - `saveEdit()` function to persist changes via API
   - `cancelEdit()` function to close without saving

2. Update **TaskCard.tsx** to use the new hook

3. Update **DayDetail.tsx** task cards to:
   - Show edit button (pencil icon) on hover
   - Expand into inline edit form when clicked
   - Include title input, description textarea, TagInput, Save/Cancel buttons

### Edit Form Fields

| Field | Type | Required |
|-------|------|----------|
| Title | text input | Yes |
| Description | textarea | No |
| Tags | TagInput component | No |

### API Call

Uses existing `taskApi.update(taskId, { title, description, tags })` endpoint.

### Query Invalidation

On successful save:
- Invalidate `['day', date]` query
- Invalidate `['tags']` query

## Implementation Plan

1. Create `useTaskEdit` hook in `frontend/src/hooks/useTaskEdit.ts`
2. Refactor TaskCard to use the hook
3. Add inline editing to DayDetail task items
4. Test editing on past, present, and future days
