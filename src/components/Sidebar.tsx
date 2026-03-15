import React from 'react'
import { LayoutDashboard, Database, BrainCircuit, BarChart2, Navigation, Zap } from 'lucide-react'

type Page = 'dashboard' | 'data-processing' | 'model-training' | 'traffic-prediction' | 'route-guidance'

interface SidebarProps {
  activePage: Page
  onNavigate: (page: Page) => void
}

const navItems: { id: Page; label: string; icon: React.ReactNode }[] = [
  { id: 'dashboard',          label: 'Dashboard',          icon: <LayoutDashboard size={17} /> },
  { id: 'data-processing',    label: 'Data Processing',    icon: <Database        size={17} /> },
  { id: 'model-training',     label: 'Model Training',     icon: <BrainCircuit    size={17} /> },
  { id: 'traffic-prediction', label: 'Traffic Prediction', icon: <BarChart2       size={17} /> },
  { id: 'route-guidance',     label: 'Route Guidance',     icon: <Navigation      size={17} /> },
]

export default function Sidebar({ activePage, onNavigate }: SidebarProps) {
  return (
    <aside className="w-64 h-screen bg-white border-r border-gray-100 flex flex-col flex-shrink-0">

      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-gray-100">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-md shadow-indigo-200">
          <Zap size={17} className="text-white" />
        </div>
        <div>
          <p className="font-bold text-gray-900 text-sm leading-none tracking-tight">TBRGS</p>
          <p className="text-xs text-gray-400 mt-0.5">Traffic Intelligence</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = activePage === item.id
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`relative w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 group ${
                isActive
                  ? 'bg-indigo-50 text-indigo-700'
                  : 'text-gray-500 hover:bg-gray-50 hover:text-gray-800'
              }`}
            >
              {/* Active left bar */}
              {isActive && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 bg-indigo-500 rounded-r-full" />
              )}
              <span className={`transition-colors ${isActive ? 'text-indigo-600' : 'text-gray-400 group-hover:text-gray-600'}`}>
                {item.icon}
              </span>
              {item.label}
            </button>
          )
        })}
      </nav>

      {/* Bottom version badge */}
      <div className="px-4 py-4 border-t border-gray-100">
        <div className="flex items-center gap-2 px-3 py-2.5 rounded-xl bg-gray-50">
          <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center flex-shrink-0">
            <Zap size={12} className="text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-gray-700 truncate">TBRGS v2.0</p>
            <p className="text-xs text-gray-400">LSTM-v4 Active</p>
          </div>
          <span className="w-2 h-2 rounded-full bg-emerald-400 flex-shrink-0" />
        </div>
      </div>

    </aside>
  )
}
