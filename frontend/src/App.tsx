import { Routes, Route } from 'react-router-dom'

// Placeholder pages — will be replaced in Phase 2
function Today() { return <div className="p-4 text-gray-800">Today's Dashboard (coming soon)</div> }
function Calendar() { return <div className="p-4 text-gray-800">Calendar (coming soon)</div> }
function Analytics() { return <div className="p-4 text-gray-800">Analytics (coming soon)</div> }

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/" element={<Today />} />
        <Route path="/calendar" element={<Calendar />} />
        <Route path="/analytics" element={<Analytics />} />
      </Routes>
    </div>
  )
}
