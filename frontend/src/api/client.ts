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
