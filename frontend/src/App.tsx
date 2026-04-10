import React, { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { NotificationPopup } from './components/NotificationPopup'

const Today = lazy(() => import('./pages/Today').then(m => ({ default: m.Today })))
const Analytics = lazy(() => import('./pages/Analytics').then(m => ({ default: m.Analytics })))
const DayDetail = lazy(() => import('./pages/DayDetail').then(m => ({ default: m.DayDetail })))
const Tags = lazy(() => import('./pages/Tags').then(m => ({ default: m.Tags })))
const TagDetail = lazy(() => import('./pages/TagDetail').then(m => ({ default: m.TagDetail })))
const Backlog = lazy(() => import('./pages/Backlog').then(m => ({ default: m.Backlog })))
const Goals = lazy(() => import('./pages/Goals').then(m => ({ default: m.Goals })))
const Settings = lazy(() => import('./pages/Settings').then(m => ({ default: m.Settings })))
import { useNotifications } from './hooks/useNotifications'
import { useNotificationMute } from './hooks/useNotificationMute'

// GlobalNotifications and NotificationBell each call useNotifications independently.
// TanStack Query deduplicates the network requests via shared cache keys.
// shownIds state is intentionally local to this component — it gates popup display only.
function GlobalNotifications() {
  const { popupNotification, markPopupShown } = useNotifications()
  const { muted } = useNotificationMute()
  if (!popupNotification || muted) return null
  return (
    <NotificationPopup
      notification={popupNotification}
      onDismiss={() => markPopupShown(popupNotification.id)}
    />
  )
}

export default function App() {
  return (
    <>
      <GlobalNotifications />
      <Suspense fallback={<div className="flex items-center justify-center h-screen text-stone-400">Loading...</div>}>
        <Routes>
          <Route path="/" element={<Today />} />
          <Route path="/day/:date" element={<DayDetail />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/tags" element={<Tags />} />
          <Route path="/tags/:tagName" element={<TagDetail />} />
          <Route path="/backlog" element={<Backlog />} />
          <Route path="/goals" element={<Goals />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </>
  )
}
