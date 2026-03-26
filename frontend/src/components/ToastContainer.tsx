import { useEffect } from 'react'
import { CheckCircle, XCircle, Info, X } from 'lucide-react'

export type ToastType = 'success' | 'error' | 'info'

export interface Toast {
  id: string
  type: ToastType
  message: string
}

interface ToastItemProps {
  toast: Toast
  onDismiss: (id: string) => void
}

function ToastItem({ toast, onDismiss }: ToastItemProps) {
  useEffect(() => {
    const t = setTimeout(() => onDismiss(toast.id), 3500)
    return () => clearTimeout(t)
  }, [toast.id, onDismiss])

  const styles = {
    success: { bg: 'bg-emerald-50 border-emerald-200', icon: <CheckCircle size={15} className="text-emerald-500 flex-shrink-0 mt-0.5" /> },
    error:   { bg: 'bg-red-50 border-red-200',     icon: <XCircle    size={15} className="text-red-500 flex-shrink-0 mt-0.5"     /> },
    info:    { bg: 'bg-indigo-50 border-indigo-200', icon: <Info      size={15} className="text-indigo-500 flex-shrink-0 mt-0.5"  /> },
  }
  const s = styles[toast.type]

  return (
    <div
      className={`flex items-start gap-2.5 px-4 py-3 rounded-xl border shadow-lg text-sm font-medium text-gray-700 max-w-xs animate-slide-in ${s.bg}`}
      style={{ animation: 'slideIn 0.2s ease-out' }}
    >
      {s.icon}
      <span className="flex-1">{toast.message}</span>
      <button onClick={() => onDismiss(toast.id)} className="text-gray-400 hover:text-gray-600 transition-colors ml-1">
        <X size={13} />
      </button>
    </div>
  )
}

interface ToastContainerProps {
  toasts: Toast[]
  onDismiss: (id: string) => void
}

export default function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
  if (!toasts.length) return null
  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2">
      {toasts.map(t => (
        <ToastItem key={t.id} toast={t} onDismiss={onDismiss} />
      ))}
    </div>
  )
}
