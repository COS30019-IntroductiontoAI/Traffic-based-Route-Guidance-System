import { useState, useCallback } from 'react'
import type { Toast, ToastType } from '../components/ToastContainer'

let counter = 0

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([])

  const push = useCallback((message: string, type: ToastType = 'info') => {
    const id = `toast-${++counter}`
    setToasts(prev => [...prev, { id, message, type }])
  }, [])

  const dismiss = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  return { toasts, push, dismiss }
}
