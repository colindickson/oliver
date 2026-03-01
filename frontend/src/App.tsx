import { Routes, Route } from 'react-router-dom'
import { Today } from './pages/Today'
import { Analytics } from './pages/Analytics'
import { DayDetail } from './pages/DayDetail'
import { Tags } from './pages/Tags'
import { TagDetail } from './pages/TagDetail'
import { Backlog } from './pages/Backlog'
import { Goals } from './pages/Goals'
import { Settings } from './pages/Settings'
import { NotificationPopup } from './components/NotificationPopup'
import { useNotifications } from './hooks/useNotifications'

function GlobalNotifications() {
  const { popupNotification, markPopupShown } = useNotifications()
  if (!popupNotification) return null
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
      <Routes>
        <Route path="/" element={<Today />} />
        <Route path="/day/:date" element={<DayDetail />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/tags" element={<Tags />} />
        <Route path="/tags/:tagName" element={<TagDetail />} />
        <Route path="/backlog" element={<Backlog />} />
        <Route path="/goals" element={<Goals />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </>
  )
}
