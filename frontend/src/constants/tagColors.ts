export const TAG_ORDER = ['commit', 'pr', 'review', 'research', 'untyped'] as const
export type TagName = typeof TAG_ORDER[number]

export const TAG_COLORS: Record<string, string> = {
  commit:   '#5b5bd6',
  pr:       '#e86b3a',
  review:   '#4a8a4a',
  research: '#d97706',
  untyped:  '#a8a29e',
}

export const TAG_BG: Record<string, string> = {
  commit:   '#ede9fe',
  pr:       '#ffedd5',
  review:   '#dcfce7',
  research: '#fef3c7',
  untyped:  '#f5f5f4',
}

export const TAG_TEXT: Record<string, string> = {
  commit:   '#5b5bd6',
  pr:       '#e86b3a',
  review:   '#4a8a4a',
  research: '#d97706',
  untyped:  '#78716c',
}
