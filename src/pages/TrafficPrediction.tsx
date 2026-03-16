import React, { useState, useMemo } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, ReferenceLine,
} from 'recharts'
import { TrendingUp, TrendingDown, Clock, AlertTriangle } from 'lucide-react'
import { useApp } from '../App'
import { themeHex } from '../theme'

const generatePrediction = (intersection: string, timeframe: string) => {
  const hours = timeframe === '6 Hours' ? 6 : timeframe === '12 Hours' ? 12 : timeframe === '48 Hours' ? 48 : 24
  const data = []
  for (let h = 0; h < hours; h++) {
    const label = `${(h % 24).toString().padStart(2, '0')}:00`
    let base = 50
    const hh = h % 24
    if (hh >= 7 && hh <= 9)   base = 600 + Math.random() * 200
    else if (hh >= 11 && hh <= 13) base = 750 + Math.random() * 150
    else if (hh >= 17 && hh <= 19) base = 820 + Math.random() * 180
    else if (hh >= 22 || hh <= 4)  base = 50  + Math.random() * 50
    else base = 200 + Math.random() * 200
    data.push({
      time: label,
      predicted: Math.round(base),
      actual: Math.round(base * (0.93 + Math.random() * 0.12)),
    })
  }
  return data
}

const intersections = ['SCATS 4021', 'SCATS 4035', 'SCATS 4051', 'SCATS 4063', 'SCATS 4078']
const timeframes    = ['6 Hours', '12 Hours', '24 Hours', '48 Hours']
const models        = ['LSTM', 'GRU', 'Random Forest', 'SVR']

export default function TrafficPrediction() {
  const { toast } = useApp()
  const [intersection, setIntersection] = useState('SCATS 4021')
  const [timeframe, setTimeframe]       = useState('24 Hours')
  const [model, setModel]               = useState('LSTM')
  const [data, setData]                 = useState(() => generatePrediction('SCATS 4021', '24 Hours'))
  const [loading, setLoading]           = useState(false)

  const handlePredict = () => {
    setLoading(true)
    toast(`Running ${model} prediction for ${intersection}...`, 'info')
    setTimeout(() => {
      setData(generatePrediction(intersection, timeframe))
      setLoading(false)
      toast(`Prediction complete for ${intersection}`, 'success')
    }, 800)
  }

  // Derived stats
  const stats = useMemo(() => {
    if (!data.length) return null
    const maxRow   = data.reduce((a, b) => a.predicted > b.predicted ? a : b)
    const minRow   = data.reduce((a, b) => a.predicted < b.predicted ? a : b)
    const avgPred  = Math.round(data.reduce((s, d) => s + d.predicted, 0) / data.length)
    const avgErr   = (data.reduce((s, d) => s + Math.abs(d.predicted - d.actual), 0) / data.length).toFixed(1)
    return { maxRow, minRow, avgPred, avgErr }
  }, [data])

  const errorData = data
    .map(d => ({ time: d.time, error: Math.abs(d.predicted - d.actual) }))
    .filter((_, i) => i % 2 === 0)

  const avgPredicted = stats?.avgPred ?? 0

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Traffic Prediction</h1>
        <p className="text-sm text-gray-400 mt-1">Predict traffic volume for SCATS intersections.</p>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-2xl border border-gray-100 p-5">
        <div className="flex items-end gap-4">
          <div className="flex-1">
            <label className="block text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wide">Intersection</label>
            <select value={intersection} onChange={e => setIntersection(e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-200 bg-white cursor-pointer">
              {intersections.map(i => <option key={i}>{i}</option>)}
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wide">Timeframe</label>
            <select value={timeframe} onChange={e => setTimeframe(e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-200 bg-white cursor-pointer">
              {timeframes.map(t => <option key={t}>{t}</option>)}
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wide">Model</label>
            <select value={model} onChange={e => setModel(e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-200 bg-white cursor-pointer">
              {models.map(m => <option key={m}>{m}</option>)}
            </select>
          </div>
          <button onClick={handlePredict} disabled={loading}
            className="px-6 py-2.5 rounded-xl text-white text-sm font-semibold hover:opacity-90 active:scale-95 transition-all disabled:opacity-60 shadow-sm whitespace-nowrap"
            style={{ background: `linear-gradient(to right, ${themeHex.primary}, ${themeHex.grad})` }}>
            {loading ? 'Predicting...' : 'Predict'}
          </button>
        </div>
      </div>

      {/* Summary stat pills */}
      {stats && (
        <div className="grid grid-cols-4 gap-3">
          <div className="bg-white rounded-2xl border border-gray-100 p-4 flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-50 flex items-center justify-center flex-shrink-0">
              <TrendingUp size={16} className="text-indigo-500" />
            </div>
            <div>
              <p className="text-xs text-gray-400">Peak Volume</p>
              <p className="text-base font-bold text-gray-900">{stats.maxRow.predicted} <span className="text-xs text-gray-400 font-normal">@ {stats.maxRow.time}</span></p>
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-gray-100 p-4 flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-50 flex items-center justify-center flex-shrink-0">
              <TrendingDown size={16} className="text-emerald-500" />
            </div>
            <div>
              <p className="text-xs text-gray-400">Off-Peak Volume</p>
              <p className="text-base font-bold text-gray-900">{stats.minRow.predicted} <span className="text-xs text-gray-400 font-normal">@ {stats.minRow.time}</span></p>
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-gray-100 p-4 flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-violet-50 flex items-center justify-center flex-shrink-0">
              <Clock size={16} className="text-violet-500" />
            </div>
            <div>
              <p className="text-xs text-gray-400">Avg Volume</p>
              <p className="text-base font-bold text-gray-900">{stats.avgPred} <span className="text-xs text-gray-400 font-normal">vehicles/h</span></p>
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-gray-100 p-4 flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-50 flex items-center justify-center flex-shrink-0">
              <AlertTriangle size={16} className="text-amber-500" />
            </div>
            <div>
              <p className="text-xs text-gray-400">Avg Error</p>
              <p className="text-base font-bold text-gray-900">{stats.avgErr} <span className="text-xs text-gray-400 font-normal">vehicles</span></p>
            </div>
          </div>
        </div>
      )}

      {/* Prediction chart */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="font-semibold text-gray-900">Predicted Traffic Volume</h2>
            <p className="text-xs text-gray-400 mt-0.5">{intersection} — Actual vs Predicted</p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-lg"
            style={{ color: themeHex.primary, backgroundColor: themeHex.primary50 }}>{model}</span>
        </div>
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="predGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor={themeHex.chart} stopOpacity={0.18} />
                <stop offset="95%" stopColor={themeHex.chart} stopOpacity={0.01} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
            <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} interval={Math.floor(data.length / 8)} />
            <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ borderRadius: '10px', border: '1px solid #e5e7eb', fontSize: 12 }} />
            <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
            <ReferenceLine y={avgPredicted} stroke="#e5e7eb" strokeDasharray="5 3"
              label={{ value: 'avg', position: 'right', fontSize: 9, fill: '#d1d5db' }} />
            <Area type="monotone" dataKey="predicted" name="Predicted" stroke={themeHex.chart} strokeWidth={2.5} fill="url(#predGrad)" />
            <Area type="monotone" dataKey="actual"    name="Actual"    stroke="#9ca3af" strokeWidth={1.5} fill="none" strokeDasharray="4 3" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Variance Analysis */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6">
        <h2 className="font-semibold text-gray-900">Variance Analysis</h2>
        <p className="text-xs text-gray-400 mt-0.5 mb-4">Prediction error by time interval</p>
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={errorData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
            <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ borderRadius: '10px', border: '1px solid #e5e7eb', fontSize: 12 }}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              formatter={(v: any) => [`${v} vehicles`, 'Error']} />
            <Bar dataKey="error" name="Error" fill="#e0e7ff" radius={[4, 4, 0, 0]} maxBarSize={24} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
