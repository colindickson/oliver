import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '../test-utils'
import { GoalDetail } from './GoalDetail'
import type { GoalDetail as GoalDetailType, Task } from '../api/client'
import { goalApi, taskApi } from '../api/client'

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
    taskApi: { ...actual.taskApi, moveToBacklog: vi.fn() },
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

  it('clears the target date via clear_target_date (not a CLEAR sentinel)', async () => {
    vi.mocked(goalApi.getOne).mockResolvedValue(detail({
      id: 1, title: 'Parent', target_date: '2026-07-01',
    }))
    vi.mocked(goalApi.update).mockResolvedValue(detail({ id: 1, title: 'Parent' }))
    renderWithProviders(<GoalDetail goalId={1} />)
    await screen.findByText('Parent')

    await userEvent.click(screen.getByRole('button', { name: 'Clear' }))

    await waitFor(() =>
      expect(goalApi.update).toHaveBeenCalledWith(1, { clear_target_date: true }),
    )
  })
})

function task(partial: Partial<Task> & { id: number; title: string }): Task {
  return {
    day_id: 9, category: 'deep_work', description: null, status: 'pending',
    order_index: 0, completed_at: null, tags: [],
    rolled_from_task_id: null, rolled_from_date: null,
    rolled_to_task_id: null, rolled_to_date: null, ...partial,
  }
}

describe('GoalDetail move to backlog', () => {
  // Goal tasks stuck on past days never appear in the main page's backlog
  // picker; moving them to the backlog is how they become pickable again.
  it('moves an unfinished scheduled task to the backlog', async () => {
    vi.mocked(goalApi.getOne).mockResolvedValue(detail({
      id: 1, title: 'Goal', tasks: [task({ id: 7, title: 'Stuck task' })],
    }))
    vi.mocked(taskApi.moveToBacklog).mockResolvedValue(task({ id: 7, title: 'Stuck task', day_id: null }))
    renderWithProviders(<GoalDetail goalId={1} />)
    await screen.findByText('Stuck task')

    await userEvent.click(screen.getByRole('button', { name: /move to backlog/i }))

    await waitFor(() => expect(taskApi.moveToBacklog).toHaveBeenCalledWith(7))
  })

  it('offers it only for unfinished tasks that are on a day and only when editable', async () => {
    vi.mocked(goalApi.getOne).mockResolvedValue(detail({
      id: 1, title: 'Goal', tasks: [
        task({ id: 1, title: 'Already backlog', day_id: null }),
        task({ id: 2, title: 'Done', status: 'completed' }),
        task({ id: 3, title: 'Rolled', status: 'rolled_forward' }),
      ],
    }))
    renderWithProviders(<GoalDetail goalId={1} />)
    await screen.findByText('Already backlog')
    expect(screen.queryByRole('button', { name: /move to backlog/i })).not.toBeInTheDocument()
  })

  it('is hidden on a read-only (archived) goal', async () => {
    vi.mocked(goalApi.getOne).mockResolvedValue(detail({
      id: 1, title: 'Goal', tasks: [task({ id: 7, title: 'Stuck task' })],
    }))
    renderWithProviders(<GoalDetail goalId={1} readOnly />)
    await screen.findByText('Stuck task')
    expect(screen.queryByRole('button', { name: /move to backlog/i })).not.toBeInTheDocument()
  })
})
