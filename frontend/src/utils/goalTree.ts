import type { Goal } from '../api/client'

export interface GoalTreeNode {
  goal: Goal
  children: Goal[]
}

/**
 * Group a flat goal list into top-level nodes with their direct sub-goals.
 * A sub-goal whose parent is not present in the list is surfaced at top level
 * so it never disappears.
 */
export function buildGoalTree(goals: Goal[]): GoalTreeNode[] {
  const byId = new Set(goals.map(g => g.id))
  const childrenOf = new Map<number, Goal[]>()
  for (const g of goals) {
    if (g.parent_goal_id != null && byId.has(g.parent_goal_id)) {
      const arr = childrenOf.get(g.parent_goal_id) ?? []
      arr.push(g)
      childrenOf.set(g.parent_goal_id, arr)
    }
  }
  return goals
    .filter(g => g.parent_goal_id == null || !byId.has(g.parent_goal_id))
    .map(g => ({ goal: g, children: childrenOf.get(g.id) ?? [] }))
}
