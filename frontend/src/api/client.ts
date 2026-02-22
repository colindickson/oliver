import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export interface Task {
  id: number
  day_id: number
  category: 'deep_work' | 'short_task' | 'maintenance'
  title: string
  description: string | null
  status: 'pending' | 'in_progress' | 'completed'
  order_index: number
  completed_at: string | null
}

export interface DayResponse {
  id: number
  date: string
  created_at: string
  tasks: Task[]
}

export interface CreateTaskPayload {
  day_id: number
  category: Task['category']
  title: string
  description?: string
  order_index?: number
}

export const dayApi = {
  getToday: () => api.get<DayResponse>('/days/today').then(r => r.data),
  getByDate: (date: string) => api.get<DayResponse>(`/days/${date}`).then(r => r.data),
}

export const taskApi = {
  create: (payload: CreateTaskPayload) =>
    api.post<Task>('/tasks', payload).then(r => r.data),
  update: (id: number, payload: Partial<Pick<Task, 'title' | 'description'>>) =>
    api.put<Task>(`/tasks/${id}`, payload).then(r => r.data),
  delete: (id: number) =>
    api.delete(`/tasks/${id}`).then(r => r.data),
  setStatus: (id: number, status: Task['status']) =>
    api.patch<Task>(`/tasks/${id}/status`, { status }).then(r => r.data),
}

export interface TimerState {
  status: 'idle' | 'running' | 'paused'
  task_id: number | null
  elapsed_seconds: number
  accumulated_seconds: number
}

export interface TimerSession {
  id: number
  task_id: number
  started_at: string
  ended_at: string | null
  duration_seconds: number | null
}

export const timerApi = {
  getCurrent: () => api.get<TimerState>('/timer/current').then(r => r.data),
  start: (task_id: number) => api.post<TimerState>('/timer/start', { task_id }).then(r => r.data),
  pause: () => api.post<TimerState>('/timer/pause').then(r => r.data),
  stop: () => api.post<TimerSession>('/timer/stop').then(r => r.data),
  getSessions: (task_id: number) => api.get<TimerSession[]>(`/timer/sessions/${task_id}`).then(r => r.data),
}

export interface AnalyticsSummary {
  period_days: number
  total_days_tracked: number
  total_tasks: number
  completed_tasks: number
  completion_rate_pct: number
}

export interface StreaksData {
  current_streak: number
  longest_streak: number
}

export interface CategoryEntry {
  category: string
  total_seconds: number
  task_count: number
}

export interface CategoriesData {
  entries: CategoryEntry[]
}

export const analyticsApi = {
  getSummary: (days = 30) => api.get<AnalyticsSummary>(`/analytics/summary?days=${days}`).then(r => r.data),
  getStreaks: () => api.get<StreaksData>('/analytics/streaks').then(r => r.data),
  getCategories: () => api.get<CategoriesData>('/analytics/categories').then(r => r.data),
}
