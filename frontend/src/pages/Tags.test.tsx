import { describe, it, expect, vi } from 'vitest'
import { screen } from '@testing-library/react'
import { renderWithProviders } from '../test-utils'
import { Tags } from './Tags'
import { dayApi, backlogApi } from '../api/client'
import type { Task } from '../api/client'

vi.mock('../api/client', async (orig) => {
  const actual = await orig<typeof import('../api/client')>()
  return {
    ...actual,
    dayApi: { ...actual.dayApi, getAll: vi.fn() },
    backlogApi: { ...actual.backlogApi, list: vi.fn() },
  }
})

const t: Task = {
  id: 1, day_id: 3, category: 'deep_work', title: 'Stale', description: null,
  status: 'pending', order_index: 0, completed_at: null, tags: ['alpha'],
  rolled_from_task_id: null, rolled_from_date: null, rolled_to_task_id: null, rolled_to_date: null,
}

describe('Tags page', () => {
  // A stale pending task is now on a past day AND in the backlog; without
  // dedupe by id every tag count would be inflated.
  it('counts a task returned by both days and backlog once', async () => {
    const d = new Date(); d.setDate(d.getDate() - 1)
    const yesterday = d.toLocaleDateString('en-CA')
    vi.mocked(dayApi.getAll).mockResolvedValue([
      { id: 3, date: yesterday, tasks: [t] } as never,
    ])
    vi.mocked(backlogApi.list).mockResolvedValue([{ ...t, day_date: yesterday }])
    renderWithProviders(<Tags />)
    const link = (await screen.findAllByText('#alpha'))[0].closest('a')!
    expect(link.textContent).toBe('#alpha1')
  })
})
