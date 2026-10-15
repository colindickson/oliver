import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '../test-utils'
import { GoalDetail } from './GoalDetail'
import type { GoalDetail as GoalDetailType, Task, DayResponse } from '../api/client'
import { goalApi, dayApi, backlogApi } from '../api/client'

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
    dayApi: { ...actual.dayApi, getToday: vi.fn() },
    backlogApi: { ...actual.backlogApi, moveToDay: vi.fn() },
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

const TODAY = { id: 50, date: '2026-10-15' } as unknown as DayResponse

describe('GoalDetail Today button', () => {
  // The one-tap flow: an unfinished goal task (stale, future or day-less) goes
  // straight to today's column; nothing is routed through the backlog first.
  beforeEach(() => {
    vi.mocked(dayApi.getToday).mockResolvedValue(TODAY)
    vi.mocked(backlogApi.moveToDay).mockResolvedValue(task({ id: 7, title: 'x' }))
  })

  it.each([
    ['past day', 9],
    ['no day', null],
  ])('offers Today for a pending task on %s and moves it to today', async (_n, day_id) => {
    vi.mocked(goalApi.getOne).mockResolvedValue(detail({
      id: 1, title: 'Goal', tasks: [task({ id: 7, title: 'Stuck task', day_id })],
    }))
    renderWithProviders(<GoalDetail goalId={1} />)
    await screen.findByText('Stuck task')

    await userEvent.click(await screen.findByRole('button', { name: /move to today/i }))

    await waitFor(() =>
      expect(backlogApi.moveToDay).toHaveBeenCalledWith(7, { day_id: 50, category: 'deep_work' }),
    )
  })

  it('falls back to deep_work when the task has no category', async () => {
    vi.mocked(goalApi.getOne).mockResolvedValue(detail({
      id: 1, title: 'Goal', tasks: [task({ id: 7, title: 'Loose', day_id: null, category: null })],
    }))
    renderWithProviders(<GoalDetail goalId={1} />)
    await userEvent.click(await screen.findByRole('button', { name: /move to today/i }))
    await waitFor(() =>
      expect(backlogApi.moveToDay).toHaveBeenCalledWith(7, { day_id: 50, category: 'deep_work' }),
    )
  })

  it('keeps the task category when it has one', async () => {
    vi.mocked(goalApi.getOne).mockResolvedValue(detail({
      id: 1, title: 'Goal', tasks: [task({ id: 7, title: 'Quick', category: 'short_task' })],
    }))
    renderWithProviders(<GoalDetail goalId={1} />)
    await userEvent.click(await screen.findByRole('button', { name: /move to today/i }))
    await waitFor(() =>
      expect(backlogApi.moveToDay).toHaveBeenCalledWith(7, { day_id: 50, category: 'short_task' }),
    )
  })

  it('shows a static Today label, not a button, for a task already on today', async () => {
    vi.mocked(goalApi.getOne).mockResolvedValue(detail({
      id: 1, title: 'Goal', tasks: [task({ id: 7, title: 'Here', day_id: 50 })],
    }))
    renderWithProviders(<GoalDetail goalId={1} />)
    await screen.findByText('Here')
    await screen.findByText('Today')
    expect(screen.queryByRole('button', { name: /move to today/i })).not.toBeInTheDocument()
  })

  it('is not offered for completed or rolled-forward tasks', async () => {
    vi.mocked(goalApi.getOne).mockResolvedValue(detail({
      id: 1, title: 'Goal', tasks: [
        task({ id: 2, title: 'Done', status: 'completed' }),
        task({ id: 3, title: 'Rolled', status: 'rolled_forward' }),
      ],
    }))
    renderWithProviders(<GoalDetail goalId={1} />)
    await screen.findByText('Done')
    expect(screen.queryByRole('button', { name: /move to today/i })).not.toBeInTheDocument()
  })

  it('is hidden on a read-only (archived) goal', async () => {
    vi.mocked(goalApi.getOne).mockResolvedValue(detail({
      id: 1, title: 'Goal', tasks: [task({ id: 7, title: 'Stuck task' })],
    }))
    renderWithProviders(<GoalDetail goalId={1} readOnly />)
    await screen.findByText('Stuck task')
    expect(screen.queryByRole('button', { name: /move to today/i })).not.toBeInTheDocument()
  })

  it('no longer offers the superseded "→ Backlog" button', async () => {
    vi.mocked(goalApi.getOne).mockResolvedValue(detail({
      id: 1, title: 'Goal', tasks: [task({ id: 7, title: 'Stuck task' })],
    }))
    renderWithProviders(<GoalDetail goalId={1} />)
    await screen.findByText('Stuck task')
    expect(screen.queryByRole('button', { name: /backlog/i })).not.toBeInTheDocument()
  })
})
