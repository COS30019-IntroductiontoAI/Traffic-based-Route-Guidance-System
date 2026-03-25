import { useState, useEffect } from 'react'
import { PanelLeft } from 'lucide-react'

interface HeaderProps {
  title: string
}

export default function Header({ title }: HeaderProps) {
  const [time, setTime] = useState(() => new Date())

  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  const fmt = time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })

  return (
    <header className="h-14 bg-white border-b border-gray-100 flex items-center justify-between px-6 flex-shrink-0">
      <div className="flex items-center gap-3">
        <PanelLeft size={18} className="text-gray-400" />
        <span className="text-sm font-semibold text-gray-700">{title}</span>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-xs text-gray-400 font-mono tabular-nums">{fmt}</span>
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
          </span>
          <span className="text-sm text-gray-500 font-medium">System Operational</span>
        </div>
      </div>
    </header>
  )
}
