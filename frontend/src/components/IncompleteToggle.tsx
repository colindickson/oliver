interface IncompleteToggleProps {
  checked: boolean
  onChange: (checked: boolean) => void
}

export function IncompleteToggle({ checked, onChange }: IncompleteToggleProps) {
  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onChange(!checked)
    }
  }

  return (
    <label className="flex items-center gap-2 cursor-pointer select-none">
      <div
        role="switch"
        aria-checked={checked}
        tabIndex={0}
        onKeyDown={handleKeyDown}
        className={`relative w-9 h-5 rounded-full transition-colors ${
          checked ? 'bg-terracotta-500' : 'bg-stone-300 dark:bg-stone-600'
        }`}
        onClick={() => onChange(!checked)}
      >
        <div
          className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow-sm transition-transform ${
            checked ? 'translate-x-4' : 'translate-x-0'
          }`}
        />
      </div>
      <span className="text-sm text-stone-600 dark:text-stone-300">Incomplete only</span>
    </label>
  )
}
