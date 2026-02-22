import { Routes, Route } from 'react-router-dom'
import { Today } from './pages/Today'
import { Calendar } from './pages/Calendar'
import { DayDetail } from './pages/DayDetail'

function AnalyticsPage() { return <div className="flex min-h-screen"><div className="p-8 text-gray-500">Analytics — Phase 5</div></div> }

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Today />} />
      <Route path="/calendar" element={<Calendar />} />
      <Route path="/day/:date" element={<DayDetail />} />
      <Route path="/analytics" element={<AnalyticsPage />} />
    </Routes>
  )
}
