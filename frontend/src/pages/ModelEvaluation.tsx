import { useState, useEffect } from 'react'
import { themeHex } from '../theme'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from 'recharts'
import { LoaderCircle, ServerCrash } from 'lucide-react'

/* ─── API types ──────────────────────────────────────────────────────────── */

interface ModelMetric {
  model: string
  mae: number
  rmse: number
  accuracy: number
}

interface MetricsStats {
  intersections: number
  records: string
  date_range: string
}

interface MetricsResponse {
  models: ModelMetric[]
  stats: MetricsStats
}

interface TrafficPoint {
  time: string
  volume: number
}

/* ─── Fetch helpers ──────────────────────────────────────────────────────── */

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '')

async function fetchMetrics(year: string): Promise<MetricsResponse> {
  const res = await fetch(`${API_BASE}/api/metrics?data=${year}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json() as Promise<MetricsResponse>
}

async function fetchTrafficProfile(year: string): Promise<TrafficPoint[]> {
  const res = await fetch(`${API_BASE}/api/traffic-profile?data=${year}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const data = await res.json() as { profile: TrafficPoint[] }
  return data.profile
}

/* ─── Component ──────────────────────────────────────────────────────────── */

type Year = '2006' | '2014'

export default function ModelEvaluation() {
  const [activeYear, setActiveYear] = useState<Year>('2014')
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [traffic, setTraffic] = useState<TrafficPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    setMetrics(null)
    setTraffic([])

    Promise.all([fetchMetrics(activeYear), fetchTrafficProfile(activeYear)])
      .then(([m, t]) => {
        setMetrics(m)
        setTraffic(t)
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : 'Failed to load data from backend')
      })
      .finally(() => setLoading(false))
  }, [activeYear])

  const bestModel = metrics?.models[0]

  return (
    <div className="p-8 space-y-6 animate-fade-up">

      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Model Evaluation</h1>
        <p className="text-sm text-gray-400 mt-1">
          Evaluate ML model performance on SCATS traffic datasets.
        </p>
      </div>

      {/* Year tabs */}
      <div className="inline-flex bg-gray-100 p-1 rounded-xl gap-1">
        {(['2006', '2014'] as const).map((y) => (
          <button
            key={y}
            onClick={() => setActiveYear(y)}
            className={`px-5 py-1.5 rounded-lg text-sm font-semibold transition-all ${
              activeYear === y
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {y}
          </button>
        ))}
      </div>

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center py-24 text-slate-400 gap-3">
          <LoaderCircle className="w-5 h-5 animate-spin text-blue-500" />
          <span className="text-sm font-medium">Loading metrics from backend…</span>
        </div>
      )}

      {/* Error state */}
      {!loading && error && (
        <div className="flex flex-col items-center justify-center py-16 text-center gap-3">
          <ServerCrash className="w-8 h-8 text-red-400" />
          <p className="text-sm font-semibold text-slate-700">Could not load evaluation data</p>
          <p className="text-xs text-slate-400">{error}</p>
          <p className="text-xs text-slate-400">Make sure the backend server is running.</p>
        </div>
      )}

      {/* Data loaded */}
      {!loading && !error && metrics && (
        <>
          {/* Stats row */}
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'Intersections', value: `${metrics.stats.intersections} nodes` },
              { label: 'Total Records',  value: metrics.stats.records },
              { label: 'Date Range',     value: metrics.stats.date_range },
            ].map((s) => (
              <div key={s.label} className="bg-white rounded-2xl border border-gray-100 p-5">
                <p className="text-xs text-gray-400 font-medium">{s.label}</p>
                <p className="text-xl font-bold text-gray-900 mt-1">{s.value}</p>
              </div>
            ))}
          </div>

          {/* Charts */}
          <div className="grid grid-cols-2 gap-4">

            {/* Traffic volume chart */}
            <div className="bg-white rounded-2xl border border-gray-100 p-6">
              <div className="mb-4">
                <h2 className="font-semibold text-gray-900">Traffic Volume — {activeYear}</h2>
                <p className="text-xs text-gray-400 mt-0.5">Average hourly SCATS volume (across all sites)</p>
              </div>
              {traffic.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={traffic} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="trafficGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor={themeHex.chart} stopOpacity={0.2} />
                        <stop offset="95%" stopColor={themeHex.chart} stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                    <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
                    <Tooltip contentStyle={{ borderRadius: '10px', border: '1px solid #e5e7eb', fontSize: 12 }}
                      labelStyle={{ color: '#374151', fontWeight: 600 }} />
                    <Area type="monotone" dataKey="volume" stroke={themeHex.chart} strokeWidth={2.5} fill="url(#trafficGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[200px] flex items-center justify-center text-sm text-gray-400">No traffic data</div>
              )}
            </div>

            {/* Model accuracy chart */}
            <div className="bg-white rounded-2xl border border-gray-100 p-6">
              <div className="mb-4">
                <h2 className="font-semibold text-gray-900">Model Accuracy — {activeYear}</h2>
                <p className="text-xs text-gray-400 mt-0.5">Prediction accuracy per model architecture</p>
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={metrics.models} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="barGrad1" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%"   stopColor={themeHex.primary} />
                      <stop offset="100%" stopColor={themeHex.grad} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
                  <XAxis dataKey="model" tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ borderRadius: '10px', border: '1px solid #e5e7eb', fontSize: 12 }}
                    formatter={(v) => [`${v}%`, 'Accuracy']} />
                  <Bar dataKey="accuracy" fill="url(#barGrad1)" radius={[6, 6, 0, 0]} maxBarSize={48} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Model metrics table */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6">
            <h2 className="font-semibold text-gray-900 mb-4">
              Detailed Metrics — {activeYear}
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-gray-400 border-b border-gray-100">
                    <th className="text-left font-medium pb-3 pr-6">Model</th>
                    <th className="text-right font-medium pb-3 pr-6">Accuracy</th>
                    <th className="text-right font-medium pb-3 pr-6">MAE</th>
                    <th className="text-right font-medium pb-3">RMSE</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {metrics.models.map((m, i) => (
                    <tr key={m.model} className="hover:bg-gray-50 transition-colors">
                      <td className="py-3 pr-6 font-medium text-gray-800 flex items-center gap-2">
                        {i === 0 && (
                          <span
                            className="text-xs px-2 py-0.5 rounded-full font-semibold"
                            style={{ backgroundColor: themeHex.primary50, color: themeHex.primary }}
                          >
                            Best
                          </span>
                        )}
                        {m.model}
                      </td>
                      <td className="py-3 pr-6 text-right font-semibold text-gray-900">{m.accuracy}%</td>
                      <td className="py-3 pr-6 text-right text-gray-500">{m.mae.toFixed(3)}</td>
                      <td className="py-3 text-right text-gray-500">{m.rmse.toFixed(3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {bestModel && (
              <p className="mt-4 text-xs text-gray-400">
                Best model:{' '}
                <span className="font-semibold text-gray-600">{bestModel.model}</span> —
                Accuracy {bestModel.accuracy}%, MAE {bestModel.mae.toFixed(3)}, RMSE {bestModel.rmse.toFixed(3)}
              </p>
            )}
          </div>
        </>
      )}

    </div>
  )
}
