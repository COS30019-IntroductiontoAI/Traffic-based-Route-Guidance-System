import { NavLink } from 'react-router-dom'
import { themeHex } from '../theme'

const navItems = [
  { to: '/route-guidance',   label: 'Route Guidance'   },
  { to: '/model-evaluation', label: 'Model Evaluation' },
  { to: '/data-insight',     label: 'Data Insight'     },
  { to: '/about-us',         label: 'About Us'         },
]

interface SidebarProps {
  activePath: string
}

export default function Sidebar({ activePath: _ }: SidebarProps) {
  return (
    <aside className="w-56 h-screen bg-white border-r border-gray-100 flex flex-col flex-shrink-0">

      {/* Brand name only — no logo icon */}
      <div className="px-5 py-5 border-b border-gray-100">
        <p className="font-bold text-gray-900 text-sm leading-none tracking-tight">TBRGS</p>
        <p className="text-xs text-gray-400 mt-1">Traffic Intelligence</p>
      </div>

      {/* Nav — text only, no icons */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `relative w-full flex items-center px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                isActive
                  ? ''
                  : 'text-gray-500 hover:bg-gray-50'
              }`
            }
            style={({ isActive }) =>
              isActive
                ? { backgroundColor: themeHex.primary50, color: themeHex.primary }
                : {}
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <span
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 rounded-r-full"
                    style={{ backgroundColor: themeHex.primary }}
                  />
                )}
                {item.label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom version — text only */}
      <div className="px-4 py-4 border-t border-gray-100">
        <div className="px-3 py-2.5 rounded-xl bg-gray-50 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-700">TBRGS v2.0</p>
            <p className="text-xs text-gray-400">LSTM-v4 Active</p>
          </div>
          <span className="w-2 h-2 rounded-full bg-emerald-400 flex-shrink-0" />
        </div>
      </div>

    </aside>
  )
}
