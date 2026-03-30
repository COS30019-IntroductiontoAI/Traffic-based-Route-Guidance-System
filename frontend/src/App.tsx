import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import RouteGuidance from './pages/RouteGuidance'
import ModelEvaluation from './pages/ModelEvaluation'
import DataInsight from './pages/DataInsight'
import AboutUs from './pages/AboutUs'
import ToastContainer from './components/ToastContainer'
import { useToast } from './hooks/useToast'
import { createContext, useContext, useCallback } from 'react'
import type { ToastType } from './components/ToastContainer'

interface AppContextValue {
  toast: (message: string, type?: ToastType) => void
}

// eslint-disable-next-line react-refresh/only-export-components
export const AppContext = createContext<AppContextValue>({ toast: () => {} })
// eslint-disable-next-line react-refresh/only-export-components
export const useApp = () => useContext(AppContext)

export default function App() {
  const { toasts, push, dismiss } = useToast()
  const location = useLocation()

  const toast = useCallback((msg: string, type: ToastType = 'info') => push(msg, type), [push])

  return (
    <AppContext.Provider value={{ toast }}>
      <div className="flex h-screen bg-gray-50 overflow-hidden">
        <Sidebar activePath={location.pathname} />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/route-guidance" replace />} />
            <Route path="/route-guidance" element={<RouteGuidance />} />
            <Route path="/model-evaluation" element={<ModelEvaluation />} />
            <Route path="/data-insight" element={<DataInsight />} />
            <Route path="/about-us" element={<AboutUs />} />
            <Route path="*" element={<Navigate to="/route-guidance" replace />} />
          </Routes>
        </main>
        <ToastContainer toasts={toasts} onDismiss={dismiss} />
      </div>
    </AppContext.Provider>
  )
}
