import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '../test-utils'
import { GoalDetail } from './GoalDetail'
import type { GoalDetail as GoalDetailType } from '../api/client'
import { goalApi } from '../api/client'

vi.mock('../api/client', async (orig) => {
  const actual = await orig<typeof import('../api/client')>()
  return {
    ...actual,
    goalApi: {
      ...actual.goalApi,
      getOne: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      setStatus: vi.fn(),
      archive: vi.fn(),
      unarchive: vi.fn(),
    },
  }
})

function detail(partial: Partial<GoalDetailType> & { id: number; title: string }): GoalDetailType {
  return {
    description: null, target_date: null, status: 'active',
    completed_at: null, archived_at: null, created_at: '2026-01-01',
    tags: [], parent_goal_id: null, sub_goal_count: 0,
    total_tasks: 0, completed_tasks: 0, progress_pct: 0,
    direct_total_tasks: 0, direct_completed_tasks: 0, direct_progress_pct: 0,
    tasks: [], sub_goals: [], ...partial,
  }
}

beforeEach(() => vi.clearAllMocks())

describe('GoalDetail sub-goals', () => {
  it('lists sub-goals of a parent', async () => {
    vi.mocked(goalApi.getOne).mockResolvedValue(detail({
      id: 1, title: 'Parent', sub_goal_count: 1,
      sub_goals: [detail({ id: 2, title: 'Child', progress_pct: 25 })],
    }))
    renderWithProviders(<GoalDetail goalId={1} />)
    expect(await screen.findByText('Child')).toBeInTheDocument()
  })

  it('hides the add-sub-goal control for a goal that is itself a sub-goal', async () => {
    vi.mocked(goalApi.getOne).mockResolvedValue(detail({
      id: 2, title: 'Child', parent_goal_id: 1,
    }))
    renderWithProviders(<GoalDetail goalId={2} />)
    await screen.findByText('Child')
    expect(screen.queryByText(/add sub-goal/i)).not.toBeInTheDocument()
  })

  it('creates a sub-goal with the parent id', async () => {
    vi.mocked(goalApi.getOne).mockResolvedValue(detail({ id: 1, title: 'Parent' }))
    vi.mocked(goalApi.create).mockResolvedValue(detail({ id: 5, title: 'New sub', parent_goal_id: 1 }))
    renderWithProviders(<GoalDetail goalId={1} />)
    await screen.findByText('Parent')

    await userEvent.click(screen.getByText(/add sub-goal/i))
    const input = screen.getByPlaceholderText(/sub-goal title/i)
    await userEvent.type(input, 'New sub{enter}')

    await waitFor(() =>
      expect(goalApi.create).toHaveBeenCalledWith(
        expect.objectContaining({ title: 'New sub', parent_goal_id: 1 }),
      ),
    )
  })

  it('detaches a sub-goal via clear_parent', async () => {
    vi.mocked(goalApi.getOne).mockResolvedValue(detail({
      id: 1, title: 'Parent', sub_goal_count: 1,
      sub_goals: [detail({ id: 2, title: 'Child', progress_pct: 25 })],
    }))
    vi.mocked(goalApi.update).mockResolvedValue(detail({ id: 2, title: 'Child' }))
    renderWithProviders(<GoalDetail goalId={1} />)
    await screen.findByText('Child')

    // The detach control is an icon button labelled "Detach to top-level"
    await userEvent.click(screen.getByRole('button', { name: /detach to top-level/i }))

    await waitFor(() =>
      expect(goalApi.update).toHaveBeenCalledWith(2, { clear_parent: true }),
    )
  })
})
