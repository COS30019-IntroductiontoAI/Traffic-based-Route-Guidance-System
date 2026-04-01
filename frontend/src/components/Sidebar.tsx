import { NavLink } from 'react-router-dom';
import { themeHex } from '../theme';
import { useState, useMemo } from 'react';
import logo from '../../public/logo.png';
import { FaRoute, FaChartBar, FaDatabase, FaInfoCircle } from 'react-icons/fa';
import { IoIosArrowForward, IoIosArrowBack } from "react-icons/io";

const navItems = [
  { to: '/route-guidance', label: 'Route Guidance', icon: <FaRoute /> },
  { to: '/model-evaluation', label: 'Model Evaluation', icon: <FaChartBar /> },
  { to: '/data-insight', label: 'Data Insight', icon: <FaDatabase /> },
  { to: '/about-us', label: 'About Us', icon: <FaInfoCircle /> },
];

interface SidebarProps {
  activePath: string;
}

export default function Sidebar({ activePath: _ }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const sidebarWidth = useMemo(() => (isCollapsed ? 'w-16' : 'w-56'), [isCollapsed]);

  return (
    <aside
      className={`relative h-screen bg-white border-r border-gray-100 flex flex-col flex-shrink-0 transition-all duration-300 ease-out will-change-auto ${sidebarWidth}`}
      style={{ willChange: 'width' }}
    >
      {/* Floating Collapse Button */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute left-full top-1/2 transform -translate-y-1/2 -translate-x-1/2 bg-white rounded-full w-8 h-8 shadow-lg p-2 hover:bg-gray-50 transition-all duration-300 z-10 border border-gray-200 flex items-center justify-center will-change-transform"
        style={{ willChange: 'transform' }}
        aria-label="Toggle sidebar"
      >
        <span className="text-gray-600 text-sm">{isCollapsed ? <IoIosArrowForward /> : <IoIosArrowBack />}</span>
      </button>

      {/* Brand Logo */}
      <div className="px-5 py-5 border-b border-gray-100 flex items-center justify-center transition-all duration-300" style={{ willChange: 'contents' }}>
        {isCollapsed ? (
          <img src={logo} alt="Logo" className="w-8 h-8 object-contain flex-shrink-0" />
        ) : (
          <div className="flex-1 truncate">
            <p className="font-bold text-gray-900 text-sm leading-none tracking-tight">TBRGS</p>
            <p className="text-xs text-gray-400 mt-1">Traffic Intelligence</p>
          </div>
        )}
      </div>

      {/* Nav Items */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => {
              const baseClass = 'relative w-full flex items-center px-3 py-2.5 rounded-xl text-sm font-medium transition-colors duration-150';
              return isActive 
                ? baseClass
                : `${baseClass} text-gray-500 hover:bg-gray-50`;
            }}
            style={({ isActive }) =>
              isActive
                ? { backgroundColor: themeHex.primary50, color: themeHex.primary }
                : {}
            }
          >
            {({ isActive }) => (
              <>
                {isActive && !isCollapsed && (
                  <span
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 rounded-r-full transition-opacity duration-150"
                    style={{ backgroundColor: themeHex.primary }}
                  />
                )}
                <span className="mr-3 flex-shrink-0">{item.icon}</span>
                {!isCollapsed && <span className="truncate">{item.label}</span>}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom Version */}
      <div className="px-4 py-4 border-t border-gray-100 transition-all duration-300" style={{ willChange: 'contents' }}>
        <div className={`px-3 py-2.5 rounded-xl bg-gray-50 flex items-center transition-all duration-300 ${isCollapsed ? 'justify-center' : 'justify-between'}`}>
          {!isCollapsed && (
            <div className="min-w-0">
              <p className="text-xs font-semibold text-gray-700">TBRGS v2.0</p>
              <p className="text-xs text-gray-400">LSTM-v4 Active</p>
            </div>
          )}
          <span className="w-2 h-2 rounded-full bg-emerald-400 flex-shrink-0" />
        </div>
      </div>
    </aside>
  );
}
