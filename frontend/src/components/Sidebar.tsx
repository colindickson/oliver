import { NavLink } from 'react-router-dom'

interface NavItem {
  to: string
  label: string
}

const links: NavItem[] = [
  { to: '/', label: 'Today' },
  { to: '/calendar', label: 'Calendar' },
  { to: '/analytics', label: 'Analytics' },
]

export function Sidebar() {
  return (
    <aside className="w-48 min-h-screen bg-slate-900 text-white flex flex-col py-8 px-4 flex-shrink-0">
      <h1 className="text-xl font-bold mb-8 text-white tracking-tight">Oliver</h1>
      <nav className="flex flex-col gap-1">
        {links.map(link => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === '/'}
            className={({ isActive }) =>
              `px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
