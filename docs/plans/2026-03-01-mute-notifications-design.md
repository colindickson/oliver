# Mute Notifications Design

**Date:** 2026-03-01

## Overview

Add a mute toggle to the notification bell dropdown. When muted, popup notifications are suppressed — the bell badge and dropdown list remain unaffected. The timer auto-activates mute when running and deactivates it when paused or stopped.

## State & Hook

New `useNotificationMute` hook:
- Reads/writes a `notifications_muted` boolean in `localStorage`
- Exposes `{ muted, setMuted, toggleMuted }`
- Watches `timer.status` via `useEffect` (timer already polls every 1s):
  - `'running'` → `setMuted(true)`
  - `'paused'` or `'idle'` → `setMuted(false)`

## Bell Dropdown Toggle

At the bottom of the `NotificationBell` dropdown, below the notification list and a divider:
- Bell-slash SVG icon on the left
- Label: "Mute notifications"
- Small toggle switch on the right showing current state
- Clicking the row toggles mute

The bell icon in the sidebar shows a subtle visual indicator (slash or muted color) when muted, so state is visible without opening the dropdown.

## Popup Suppression

`GlobalNotifications` in `App.tsx`:
- Calls `useNotificationMute()` alongside `useNotifications()`
- Skips rendering `NotificationPopup` when `muted` is true
- Bell badge count and dropdown list are unaffected

## Files Affected

- `frontend/src/hooks/useNotificationMute.ts` — new hook
- `frontend/src/components/NotificationBell.tsx` — add toggle row + muted bell indicator
- `frontend/src/App.tsx` — suppress popup when muted
