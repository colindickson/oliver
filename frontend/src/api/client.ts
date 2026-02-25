import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export interface Task {
  id: number
  day_id: number | null  // nullable for backlog tasks
  category: 'deep_work' | 'short_task' | 'maintenance' | null  // nullable for backlog
  title: string
  description: string | null
  status: 'pending' | 'in_progress' | 'completed'
  order_index: number
  completed_at: string | null
  tags: string[]
}

export interface CreateBacklogTaskPayload {
  title: string
  description?: string
  category?: 'deep_work' | 'short_task' | 'maintenance'
  tags?: string[]
}

export interface MoveToDayPayload {
  day_id: number
  category?: 'deep_work' | 'short_task' | 'maintenance'
}

export interface DailyNote {
  id: number
  day_id: number
  content: string
  updated_at: string
}

export interface Roadblock {
  id: number
  day_id: number
  content: string
  updated_at: string
}

export interface DayRating {
  id: number
  day_id: number
  focus: number | null
  energy: number | null
  satisfaction: number | null
}

export type WeatherCondition = 'sunny' | 'partly_cloudy' | 'cloudy' | 'rainy' | 'snowy' | 'stormy' | 'foggy'
export type MoonPhase =
  | 'new_moon' | 'waxing_crescent' | 'first_quarter' | 'waxing_gibbous'
  | 'full_moon' | 'waning_gibbous' | 'last_quarter' | 'waning_crescent'

export interface DayMetadata {
  id: number
  day_id: number
  temperature_c: number | null
  condition: WeatherCondition | null
  moon_phase: MoonPhase | null
}

export interface DayResponse {
  id: number
  date: string
  created_at: string
  tasks: Task[]
  notes: DailyNote | null
  roadblocks: Roadblock | null
  rating: DayRating | null
  day_metadata: DayMetadata | null
}

export interface CreateTaskPayload {
  day_id: number
  category: Task['category']
  title: string
  description?: string
  order_index?: number
  tags?: string[]
}

export const dayApi = {
  getToday: () => api.get<DayResponse>('/days/today').then(r => r.data),
  getByDate: (date: string) => api.get<DayResponse>(`/days/${date}`).then(r => r.data),
  getAll: () => api.get<DayResponse[]>('/days').then(r => r.data),
  upsertNotes: (day_id: number, content: string) =>
    api.put<DailyNote>(`/days/${day_id}/notes`, { content }).then(r => r.data),
  upsertRoadblocks: (day_id: number, content: string) =>
    api.put<Roadblock>(`/days/${day_id}/roadblocks`, { content }).then(r => r.data),
  upsertRating: (day_id: number, rating: Partial<Omit<DayRating, 'id' | 'day_id'>>) =>
    api.put<DayRating>(`/days/${day_id}/rating`, rating).then(r => r.data),
  upsertMetadata: (day_id: number, meta: Omit<DayMetadata, 'id' | 'day_id'>) =>
    api.put<DayMetadata>(`/days/${day_id}/metadata`, meta).then(r => r.data),
}

export const taskApi = {
  create: (payload: CreateTaskPayload) =>
    api.post<Task>('/tasks', payload).then(r => r.data),
  update: (id: number, payload: Partial<Pick<Task, 'title' | 'description'>> & { tags?: string[] }) =>
    api.put<Task>(`/tasks/${id}`, payload).then(r => r.data),
  delete: (id: number) =>
    api.delete(`/tasks/${id}`).then(r => r.data),
  setStatus: (id: number, status: Task['status']) =>
    api.patch<Task>(`/tasks/${id}/status`, { status }).then(r => r.data),
  reorder: (task_ids: number[]) =>
    api.post('/tasks/reorder', { task_ids }).then(r => r.data),
  moveToBacklog: (id: number) =>
    api.post<Task>(`/tasks/${id}/move-to-backlog`).then(r => r.data),
  continueTomorrow: (id: number) =>
    api.post<Task>(`/tasks/${id}/continue-tomorrow`).then(r => r.data),
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
  addTime: (task_id: number, seconds: number) =>
    api.post<TimerSession>('/timer/add-time', { task_id, seconds }).then(r => r.data),
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

export interface TodayDeepWorkResponse {
  total_seconds: number
  goal_seconds: number
}

export const analyticsApi = {
  getSummary: (days = 30) => api.get<AnalyticsSummary>(`/analytics/summary?days=${days}`).then(r => r.data),
  getStreaks: () => api.get<StreaksData>('/analytics/streaks').then(r => r.data),
  getCategories: () => api.get<CategoriesData>('/analytics/categories').then(r => r.data),
  getTodayDeepWork: () => api.get<TodayDeepWorkResponse>('/analytics/today-deep-work').then(r => r.data),
}

export interface Reminder {
  id: number
  task_id: number
  remind_at: string
  message: string
  is_delivered: boolean
}

export const reminderApi = {
  create: (task_id: number, remind_at: string, message: string) =>
    api.post<Reminder>('/reminders', { task_id, remind_at, message }).then(r => r.data),
  getDue: () => api.get<Reminder[]>('/reminders/due').then(r => r.data),
  markDelivered: (id: number) =>
    api.patch<Reminder>(`/reminders/${id}/delivered`).then(r => r.data),
}

export interface TagResponse {
  id: number
  name: string
  task_count: number
}

export interface TagTaskGroup {
  date: string
  tasks: Task[]
}

export const tagApi = {
  getAll: () => api.get<TagResponse[]>('/tags').then(r => r.data),
  getTasksForTag: (name: string) =>
    api.get<TagTaskGroup[]>(`/tags/${encodeURIComponent(name)}/tasks`).then(r => r.data),
}

export const backlogApi = {
  list: (params?: { tag?: string; search?: string }) => {
    const query = new URLSearchParams()
    if (params?.tag) query.set('tag', params.tag)
    if (params?.search) query.set('search', params.search)
    const queryString = query.toString()
    return api.get<Task[]>(`/backlog${queryString ? `?${queryString}` : ''}`).then(r => r.data)
  },
  create: (payload: CreateBacklogTaskPayload) =>
    api.post<Task>('/backlog', payload).then(r => r.data),
  moveToDay: (id: number, payload: MoveToDayPayload) =>
    api.post<Task>(`/backlog/${id}/move-to-day`, payload).then(r => r.data),
}
