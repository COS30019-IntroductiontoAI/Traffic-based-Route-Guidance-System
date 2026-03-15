import React, { useState } from 'react'
import { Database, FileText, CheckCircle, RefreshCw, Clock, HardDrive, Trash2, FolderOpen } from 'lucide-react'
import StatCard from '../components/StatCard'
import { useApp } from '../App'

type DatasetStatus = 'synced' | 'processing' | 'pending'

interface Dataset {
  id: number
  name: string
  records: string
  size: string
  status: DatasetStatus
  time: string
  progress?: number
  color: string
}

const initialDatasets: Dataset[] = [
  { id: 1, name: 'SCATS Volume Data',    records: '2.4M records', size: '4.2 GB', status: 'synced',     time: '2h ago',   color: '#6366f1' },
  { id: 2, name: 'Road Network Graph',   records: '14K nodes',    size: '1.8 GB', status: 'synced',     time: '1d ago',   color: '#8b5cf6' },
  { id: 3, name: 'Historical Patterns',  records: '890K records', size: '2.1 GB', status: 'processing', time: '5m ago',   color: '#06b6d4', progress: 67 },
  { id: 4, name: 'Weather Correlation',  records: '120K records', size: '340 MB', status: 'pending',    time: '—',        color: '#f59e0b' },
]

const statusConfig: Record<DatasetStatus, { icon: React.ReactNode; label: string; textColor: string; bg: string }> = {
  synced:     { icon: <CheckCircle size={14} />, label: 'Synced',     textColor: 'text-emerald-600', bg: 'bg-emerald-50' },
  processing: { icon: <RefreshCw   size={14} className="animate-spin" />, label: 'Processing', textColor: 'text-indigo-600', bg: 'bg-indigo-50' },
  pending:    { icon: <Clock       size={14} />, label: 'Pending',    textColor: 'text-amber-600',   bg: 'bg-amber-50'   },
}

function StatusBadge({ status }: { status: DatasetStatus }) {
  const cfg = statusConfig[status]
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold ${cfg.textColor} ${cfg.bg}`}>
      {cfg.icon} {cfg.label}
    </span>
  )
}

export default function DataProcessing() {
  const [datasets, setDatasets] = useState<Dataset[]>(initialDatasets)
  const { toast } = useApp()

  const handleRefreshAll = () => {
    setDatasets(prev => prev.map(d =>
      d.status !== 'synced' ? { ...d, status: 'processing', time: 'just now', progress: 0 } : d
    ))
    toast('Refreshing all datasets...', 'info')

    // Simulate progress
    let pct = 0
    const progInterval = setInterval(() => {
      pct = Math.min(100, pct + Math.random() * 18)
      setDatasets(prev => prev.map(d =>
        d.status === 'processing' ? { ...d, progress: Math.round(pct) } : d
      ))
    }, 200)

    setTimeout(() => {
      clearInterval(progInterval)
      setDatasets(prev => prev.map(d => ({ ...d, status: 'synced', time: 'just now', progress: undefined })))
      toast('All datasets synced successfully', 'success')
    }, 2200)
  }

  const handleDelete = (id: number, name: string) => {
    setDatasets(prev => prev.filter(d => d.id !== id))
    toast(`Removed dataset: ${name}`, 'info')
  }

  const totalSynced = datasets.filter(d => d.status === 'synced').length

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Data Processing</h1>
        <p className="text-sm text-gray-400 mt-1">Manage and process traffic datasets.</p>
      </div>

      <div className="flex gap-4">
        <StatCard label="Total Size"    value="8.4 GB"   icon={<HardDrive size={22} />} />
        <StatCard label="Total Records" value="3.4M"     icon={<FileText  size={22} />} />
        <StatCard label="Data Sources"  value={`${totalSynced} / ${datasets.length} Active`} icon={<CheckCircle size={22} />} />
      </div>

      <div className="bg-white rounded-2xl border border-gray-100 p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-semibold text-gray-900">Datasets</h2>
          <span className="text-xs text-gray-400">{datasets.length} total</span>
        </div>

        {datasets.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-14 h-14 rounded-2xl bg-gray-50 border border-gray-100 flex items-center justify-center mb-4">
              <FolderOpen size={26} className="text-gray-300" />
            </div>
            <p className="text-sm font-semibold text-gray-500">No datasets loaded</p>
            <p className="text-xs text-gray-400 mt-1">Click "Load New Dataset" to get started</p>
          </div>
        ) : (
          <div className="space-y-1">
            {datasets.map((dataset) => (
              <div
                key={dataset.id}
                className="group flex items-center gap-4 px-4 py-3.5 rounded-xl hover:bg-gray-50 transition-colors border border-transparent hover:border-gray-100"
              >
                {/* Color dot */}
                <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: dataset.color }} />

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <p className="text-sm font-semibold text-gray-800 truncate">{dataset.name}</p>
                  </div>
                  <p className="text-xs text-gray-400">{dataset.records} · {dataset.size}</p>
                  {/* Progress bar for processing */}
                  {dataset.status === 'processing' && dataset.progress !== undefined && (
                    <div className="mt-2">
                      <div className="flex justify-between mb-1">
                        <span className="text-xs text-indigo-500 font-medium">Processing...</span>
                        <span className="text-xs text-indigo-500 font-semibold">{dataset.progress}%</span>
                      </div>
                      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-indigo-500 rounded-full transition-all duration-300"
                          style={{ width: `${dataset.progress}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Status + time */}
                <div className="flex-shrink-0 text-right space-y-1.5">
                  <StatusBadge status={dataset.status} />
                  <p className="text-xs text-gray-400">{dataset.time}</p>
                </div>

                {/* Delete button – shown on hover */}
                <button
                  onClick={() => handleDelete(dataset.id, dataset.name)}
                  className="flex-shrink-0 opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-red-50 text-gray-300 hover:text-red-400 transition-all"
                  title="Remove dataset"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex gap-3">
        <button
          onClick={() => {
            const newDs: Dataset = {
              id: Date.now(),
              name: `New Dataset ${datasets.length + 1}`,
              records: '0 records',
              size: '0 MB',
              status: 'pending',
              time: 'just now',
              color: '#94a3b8',
            }
            setDatasets(prev => [...prev, newDs])
            toast('New dataset slot added', 'success')
          }}
          className="px-5 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 transition-colors shadow-sm flex items-center gap-2"
        >
          <Database size={16} /> Load New Dataset
        </button>
        <button
          onClick={handleRefreshAll}
          className="px-5 py-2.5 rounded-xl bg-white border border-gray-200 text-gray-700 text-sm font-semibold hover:bg-gray-50 transition-colors flex items-center gap-2"
        >
          <RefreshCw size={16} /> Refresh All
        </button>
      </div>
    </div>
  )
}
