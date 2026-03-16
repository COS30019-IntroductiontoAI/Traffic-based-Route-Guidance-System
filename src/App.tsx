import React, { useState, createContext, useContext, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Dashboard from './pages/Dashboard'
import DataProcessing  from './pages/DataProcessing'
import ModelTraining  from './pages/ModelTraining'
import TrafficPrediction from './pages/TrafficPrediction'
import RouteGuidance  from './pages/RouteGuidance'
import ToastContainer from './components/ToastContainer'
import { useToast } from './hooks/useToast'
import type { ToastType } from './components/ToastContainer'

export type Page = 'dashboard' | 'data-processing' | 'model-training' | 'traffic-prediction' | 'route-guidance'

interface AppContextValue {
  navigate: (page: Page) => void
  toast: (message: string, type?: ToastType) => void
}
// eslint-disable-next-line react-refresh/only-export-components
export const AppContext = createContext<AppContextValue>({
  navigate: () => {},
  toast: () => {},
})
// eslint-disable-next-line react-refresh/only-export-components
export const useApp = () => useContext(AppContext)

const PAGE_TITLES: Record<Page, string> = {
  dashboard: 'Dashboard',
  'data-processing': 'Data Processing',
  'model-training': 'Model Training',
  'traffic-prediction': 'Traffic Prediction',
  'route-guidance': 'Route Guidance',
}

export default function App() {
  const [page, setPage] = useState<Page>('dashboard')
  const { toasts, push, dismiss } = useToast()

  const navigate = useCallback((p: Page) => setPage(p), [])
  const toast = useCallback((msg: string, type: ToastType = 'info') => push(msg, type), [push])

  return (
    <AppContext.Provider value={{ navigate, toast }}>
      <div className="flex h-screen bg-gray-50 overflow-hidden">
        <Sidebar activePage={page} onNavigate={setPage} />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header title={PAGE_TITLES[page]} />
          <main className="flex-1 overflow-y-auto">
            {page === 'dashboard'          && <Dashboard />}
            {page === 'data-processing'    && <DataProcessing />}
            {page === 'model-training'     && <ModelTraining />}
            {page === 'traffic-prediction' && <TrafficPrediction />}
            {page === 'route-guidance'     && <RouteGuidance />}
          </main>
        </div>
        <ToastContainer toasts={toasts} onDismiss={dismiss} />
      </div>
    </AppContext.Provider>
  )
}
