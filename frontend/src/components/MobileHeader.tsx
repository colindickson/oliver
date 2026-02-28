import { Link, useLocation } from 'react-router-dom'
import { useTheme } from '../contexts/ThemeContext'

interface MobileHeaderProps {
  title: string
}

export function MobileHeader({ title }: MobileHeaderProps) {
  const location = useLocation()
  const { theme, toggleTheme } = useTheme()

  return (
    <header className="flex items-center justify-between px-4 py-3 bg-stone-900 border-b border-stone-700/50 flex-shrink-0">
      <h1 className="font-display text-lg font-semibold text-white">{title}</h1>
      <div className="flex items-center gap-1">
        <button
          onClick={toggleTheme}
          className="w-8 h-8 flex items-center justify-center rounded-lg text-stone-400 hover:text-stone-200 hover:bg-stone-700 transition-colors"
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? (
            <svg width="16" height="16" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <circle cx="7.5" cy="7.5" r="2.5" />
              <path d="M7.5 1v1.5M7.5 12.5V14M1 7.5h1.5M12.5 7.5H14M3.05 3.05l1.06 1.06M10.9 10.9l1.06 1.06M3.05 11.95l1.06-1.06M10.9 4.1l1.06-1.06" />
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M13 8A5.6 5.6 0 1 1 7 1.9 4.4 4.4 0 0 0 13 8z" />
            </svg>
          )}
        </button>
        <Link
          to="/settings"
          className={`w-8 h-8 flex items-center justify-center rounded-lg transition-colors flex-shrink-0
            ${location.pathname === '/settings'
              ? 'text-stone-200 bg-stone-700'
              : 'text-stone-400 hover:text-stone-200 hover:bg-stone-700'
            }`}
          aria-label="Settings"
        >
          <svg width="16" height="16" viewBox="0 0 15 15" fill="none" stroke="currentColor"
               strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="1" y1="3.5" x2="14" y2="3.5" />
            <circle cx="5" cy="3.5" r="1.5" fill="currentColor" stroke="none" />
            <line x1="1" y1="7.5" x2="14" y2="7.5" />
            <circle cx="10" cy="7.5" r="1.5" fill="currentColor" stroke="none" />
            <line x1="1" y1="11.5" x2="14" y2="11.5" />
            <circle cx="5" cy="11.5" r="1.5" fill="currentColor" stroke="none" />
          </svg>
        </Link>
      </div>
    </header>
  )
}
