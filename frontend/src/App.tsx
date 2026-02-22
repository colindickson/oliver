import { Routes, Route } from 'react-router-dom'
import { Today } from './pages/Today'
import { Sidebar } from './components/Sidebar'

function CalendarPage() {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
        Calendar &mdash; Phase 6
      </div>
    </div>
  )
}

function AnalyticsPage() {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
        Analytics &mdash; Phase 5
      </div>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Today />} />
      <Route path="/calendar" element={<CalendarPage />} />
      <Route path="/analytics" element={<AnalyticsPage />} />
    </Routes>
  )
}
