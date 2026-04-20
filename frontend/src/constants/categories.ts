export const CATEGORIES = {
  deep_work: {
    key: 'deep_work',
    label: 'Deep Work',
    color: 'text-indigo-600 dark:text-indigo-400',
    bg: 'bg-indigo-50 dark:bg-indigo-900/20',
    border: 'border-indigo-200 dark:border-indigo-800/30',
    badge: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300',
    header: 'border-indigo-500 text-indigo-700 dark:text-indigo-400',
    button: 'bg-indigo-50 text-indigo-600 hover:bg-indigo-100 border-indigo-200 dark:bg-indigo-900/20 dark:text-indigo-300 dark:hover:bg-indigo-900/30 dark:border-indigo-800/30',
    tab: 'text-indigo-400 border-b-2 border-indigo-400',
    topBorder: 'border-t-indigo-500',
    progressFill: 'bg-indigo-500/60',
  },
  short_task: {
    key: 'short_task',
    label: 'Short Tasks',
    color: 'text-terracotta-600 dark:text-terracotta-400',
    bg: 'bg-terracotta-50 dark:bg-terracotta-900/20',
    border: 'border-terracotta-200 dark:border-terracotta-800/30',
    badge: 'bg-terracotta-100 text-terracotta-700 dark:bg-terracotta-900/30 dark:text-terracotta-300',
    header: 'border-terracotta-400 text-terracotta-700 dark:text-terracotta-400',
    button: 'bg-terracotta-50 text-terracotta-600 hover:bg-terracotta-100 border-terracotta-200 dark:bg-terracotta-900/20 dark:text-terracotta-300 dark:hover:bg-terracotta-900/30 dark:border-terracotta-800/30',
    tab: 'text-terracotta-400 border-b-2 border-terracotta-400',
    topBorder: 'border-t-terracotta-500',
    progressFill: 'bg-terracotta-500/60',
  },
  maintenance: {
    key: 'maintenance',
    label: 'Maintenance',
    color: 'text-moss-600 dark:text-moss-400',
    bg: 'bg-moss-50 dark:bg-moss-900/20',
    border: 'border-moss-200 dark:border-moss-800/30',
    badge: 'bg-moss-100 text-moss-700 dark:bg-moss-900/30 dark:text-moss-300',
    header: 'border-moss-400 text-moss-700 dark:text-moss-400',
    button: 'bg-moss-50 text-moss-600 hover:bg-moss-100 border-moss-200 dark:bg-moss-900/20 dark:text-moss-300 dark:hover:bg-moss-900/30 dark:border-moss-800/30',
    tab: 'text-moss-400 border-b-2 border-moss-400',
    topBorder: 'border-t-moss-500',
    progressFill: 'bg-moss-500/60',
  },
} as const

export type CategoryKey = keyof typeof CATEGORIES

export const CATEGORY_LIST = Object.values(CATEGORIES)

export const CATEGORY_LABELS: Record<string, string> = Object.fromEntries(
  Object.entries(CATEGORIES).map(([k, v]) => [k, v.label])
)

export const CATEGORY_COLORS: Record<string, string> = Object.fromEntries(
  Object.entries(CATEGORIES).map(([k, v]) => [k, v.badge])
)
