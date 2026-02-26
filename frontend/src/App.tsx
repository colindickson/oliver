import { Routes, Route } from 'react-router-dom'
import { Today } from './pages/Today'
import { Analytics } from './pages/Analytics'
import { DayDetail } from './pages/DayDetail'
import { Tags } from './pages/Tags'
import { TagDetail } from './pages/TagDetail'
import { Backlog } from './pages/Backlog'
import { Goals } from './pages/Goals'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Today />} />
      <Route path="/day/:date" element={<DayDetail />} />
      <Route path="/analytics" element={<Analytics />} />
      <Route path="/tags" element={<Tags />} />
      <Route path="/tags/:tagName" element={<TagDetail />} />
      <Route path="/backlog" element={<Backlog />} />
      <Route path="/goals" element={<Goals />} />
    </Routes>
  )
}
