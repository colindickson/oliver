import { describe, it, expect, vi } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import { renderWithProviders } from '../test-utils'
import { StaleSweep } from './Backlog'
import { backlogApi } from '../api/client'
import type { Task } from '../api/client'

vi.mock('../api/client', async (orig) => {
  const actual = await orig<typeof import('../api/client')>()
  return { ...actual, backlogApi: { ...actual.backlogApi, completeStale: vi.fn() } }
})

function daysAgo(n: number): string {
  const d = new Date(); d.setDate(d.getDate() - n)
  return d.toLocaleDateString('en-CA')
}

const base: Task = {
  id: 1, day_id: 3, category: 'deep_work', title: 'T', description: null,
  status: 'pending', order_index: 0, completed_at: null, tags: [],
  rolled_from_task_id: null, rolled_from_date: null, rolled_to_task_id: null, rolled_to_date: null,
}

describe('StaleSweep', () => {
  // The count must match what the backend sweeps (scheduled > 7 days ago),
  // so the user knows exactly how many tasks they are closing out.
  it('counts only tasks scheduled more than 7 days ago and sweeps on confirm', async () => {
    vi.mocked(backlogApi.completeStale).mockResolvedValue({ completed: 2 })
    renderWithProviders(
      <StaleSweep tasks={[
        { ...base, id: 1, day_date: daysAgo(8) },
        { ...base, id: 2, day_date: daysAgo(30), status: 'in_progress' },
        { ...base, id: 3, day_date: daysAgo(7) },
        { ...base, id: 4, day_id: null, day_date: null },
      ]} />,
    )
    fireEvent.click(screen.getByRole('button', { name: /mark 2 tasks older than 7 days done/i }))
    expect(backlogApi.completeStale).not.toHaveBeenCalled()
    fireEvent.click(screen.getByRole('button', { name: /^yes$/i }))
    await waitFor(() => expect(backlogApi.completeStale).toHaveBeenCalledWith(7))
  })

  it('renders nothing when no task is stale', () => {
    const { container } = renderWithProviders(
      <StaleSweep tasks={[{ ...base, day_date: daysAgo(2) }]} />,
    )
    expect(container).toBeEmptyDOMElement()
  })
})
