import React from 'react'

interface StatCardProps {
  label: string
  value: string
  sub?: string
  icon: React.ReactNode
  accent?: string
}

export default function StatCard({ label, value, sub, icon, accent = '#6366f1' }: StatCardProps) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5 flex items-start justify-between flex-1 hover:shadow-sm transition-shadow group">
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-400 font-medium mb-1.5 uppercase tracking-wide">{label}</p>
        <p className="text-2xl font-bold text-gray-900 truncate">{value}</p>
        {sub && <p className="text-xs text-gray-400 mt-1.5 font-mono">{sub}</p>}
      </div>
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ml-3 mt-0.5 transition-transform group-hover:scale-110"
        style={{ backgroundColor: `${accent}15`, color: accent }}
      >
        {icon}
      </div>
    </div>
  )
}
