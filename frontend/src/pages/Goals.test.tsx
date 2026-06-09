import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '../test-utils'
import { Goals } from './Goals'
import { goalApi, settingsApi } from '../api/client'
import type { Goal } from '../api/client'

vi.mock('../api/client', async (orig) => {
  const actual = await orig<typeof import('../api/client')>()
  return {
    ...actual,
    goalApi: { ...actual.goalApi, getAll: vi.fn(), getOne: vi.fn() },
    settingsApi: { ...actual.settingsApi, getFocusGoal: vi.fn(), setFocusGoal: vi.fn() },
  }
})

function goal(p: Partial<Goal> & { id: number; title: string }): Goal {
  return {
    description: null, target_date: null, status: 'active',
    completed_at: null, archived_at: null, created_at: '2026-01-01',
    tags: [], parent_goal_id: null, sub_goal_count: 0,
    total_tasks: 0, completed_tasks: 0, progress_pct: 0,
    direct_total_tasks: 0, direct_completed_tasks: 0, direct_progress_pct: 0, ...p,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(settingsApi.getFocusGoal).mockResolvedValue({ goal_id: null })
  vi.mocked(goalApi.getOne).mockResolvedValue({
    ...goal({ id: 1, title: 'Parent', sub_goal_count: 1 }), tasks: [], sub_goals: [],
  } as never)
})

describe('Goals nested list', () => {
  it('renders sub-goals nested under the parent and shows a child-count badge', async () => {
    vi.mocked(goalApi.getAll).mockResolvedValue([
      goal({ id: 1, title: 'Parent', sub_goal_count: 1 }),
      goal({ id: 2, title: 'Child', parent_goal_id: 1 }),
    ])
    renderWithProviders(<Goals />)
    expect(await screen.findByText('Parent')).toBeInTheDocument()
    expect(screen.getByText('Child')).toBeInTheDocument()
    expect(screen.getByText(/1 sub-goal/i)).toBeInTheDocument()
  })

  it('collapses and expands a parent’s sub-goals', async () => {
    vi.mocked(goalApi.getAll).mockResolvedValue([
      goal({ id: 1, title: 'Parent', sub_goal_count: 1 }),
      goal({ id: 2, title: 'Child', parent_goal_id: 1 }),
    ])
    renderWithProviders(<Goals />)
    await screen.findByText('Parent')
    expect(screen.getByText('Child')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: /collapse sub-goals/i }))
    expect(screen.queryByText('Child')).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: /expand sub-goals/i }))
    expect(screen.getByText('Child')).toBeInTheDocument()
  })
})
