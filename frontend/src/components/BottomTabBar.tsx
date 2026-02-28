import { NavLink } from 'react-router-dom'

const tabs = [
  {
    to: '/',
    label: 'Home',
    icon: (
      <svg width="22" height="22" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M1 7L7 1L13 7" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M3 5v7h3v-4h2v4h3V5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    end: true,
  },
  {
    to: '/goals',
    label: 'Goals',
    icon: (
      <svg width="22" height="22" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="7" cy="7" r="6" />
        <circle cx="7" cy="7" r="2.5" />
        <circle cx="7" cy="7" r="0.75" fill="currentColor" stroke="none" />
        <path d="M7 1v1.5M7 11.5V13M1 7h1.5M11.5 7H13" strokeLinecap="round" />
      </svg>
    ),
    end: false,
  },
  {
    to: '/backlog',
    label: 'Backlog',
    icon: (
      <svg width="22" height="22" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M2 2h10v10H2z" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M5 5h4M5 7h4M5 9h2" strokeLinecap="round" />
      </svg>
    ),
    end: false,
  },
  {
    to: '/tags',
    label: 'Tags',
    icon: (
      <svg width="22" height="22" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M1 7L7 1h5v5L7 13 1 7Z" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="9.5" cy="4.5" r="1" fill="currentColor" stroke="none" />
      </svg>
    ),
    end: false,
  },
  {
    to: '/analytics',
    label: 'Analytics',
    icon: (
      <svg width="22" height="22" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
        <polyline points="1,10 4,6 7,8 10,3 13,5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    end: false,
  },
]

export function BottomTabBar() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-stone-900 border-t border-stone-700/50 flex items-stretch">
      {tabs.map(tab => (
        <NavLink
          key={tab.to}
          to={tab.to}
          end={tab.end}
          className={({ isActive }) =>
            `flex-1 flex flex-col items-center justify-center gap-0.5 py-2 transition-colors ${
              isActive
                ? 'text-terracotta-400'
                : 'text-stone-500 hover:text-stone-300'
            }`
          }
        >
          {tab.icon}
          <span className="text-[10px] font-medium">{tab.label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
