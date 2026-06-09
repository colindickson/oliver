import { describe, it, expect } from 'vitest'
import { buildGoalTree } from './goalTree'
import type { Goal } from '../api/client'

function goal(partial: Partial<Goal> & { id: number; title: string }): Goal {
  return {
    description: null, target_date: null, status: 'active',
    completed_at: null, archived_at: null, created_at: '2026-01-01',
    tags: [], parent_goal_id: null, sub_goal_count: 0,
    total_tasks: 0, completed_tasks: 0, progress_pct: 0,
    direct_total_tasks: 0, direct_completed_tasks: 0, direct_progress_pct: 0,
    ...partial,
  }
}

describe('buildGoalTree', () => {
  it('nests sub-goals under their parent and excludes them from top level', () => {
    const goals = [
      goal({ id: 1, title: 'Parent' }),
      goal({ id: 2, title: 'Child', parent_goal_id: 1 }),
      goal({ id: 3, title: 'Standalone' }),
    ]
    const tree = buildGoalTree(goals)
    expect(tree.map(n => n.goal.title)).toEqual(['Parent', 'Standalone'])
    const parent = tree.find(n => n.goal.id === 1)!
    expect(parent.children.map(c => c.title)).toEqual(['Child'])
    const standalone = tree.find(n => n.goal.id === 3)!
    expect(standalone.children).toEqual([])
  })

  it('places an orphaned sub-goal (missing parent in list) at top level', () => {
    const goals = [goal({ id: 2, title: 'Orphan', parent_goal_id: 99 })]
    const tree = buildGoalTree(goals)
    expect(tree.map(n => n.goal.title)).toEqual(['Orphan'])
  })
})
