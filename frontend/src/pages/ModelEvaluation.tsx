import { useState } from 'react'
import { themeHex } from '../theme'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'

/* ─── Static mock data per year ─────────────────────────────────────────── */

const DATA: Record<'2006' | '2014', {
  traffic: { time: string; volume: number }[]
  models: { model: string; mae: number; rmse: number; accuracy: number }[]
  stats: { intersections: number; records: string; size: string }
}> = {
  '2006': {
    traffic: [
      { time: '00:00', volume: 95  }, { time: '03:00', volume: 60  },
      { time: '06:00', volume: 170 }, { time: '09:00', volume: 620 },
      { time: '12:00', volume: 510 }, { time: '15:00', volume: 680 },
      { time: '18:00', volume: 730 }, { time: '21:00', volume: 390 },
    ],
    models: [
      { model: 'LSTM',     mae: 0.061, rmse: 0.142, accuracy: 91.8 },
      { model: 'GRU',      mae: 0.068, rmse: 0.155, accuracy: 90.2 },
      { model: 'LightGBM', mae: 0.078, rmse: 0.171, accuracy: 87.4 },
    ],
    stats: { intersections: 12, records: '1.9M', size: '3.1 GB' },
  },
  '2014': {
    traffic: [
      { time: '00:00', volume: 120 }, { time: '03:00', volume: 80  },
      { time: '06:00', volume: 200 }, { time: '09:00', volume: 780 },
      { time: '12:00', volume: 650 }, { time: '15:00', volume: 820 },
      { time: '18:00', volume: 900 }, { time: '21:00', volume: 480 },
    ],
    models: [
      { model: 'LSTM',     mae: 0.042, rmse: 0.118, accuracy: 94.2 },
      { model: 'GRU',      mae: 0.051, rmse: 0.131, accuracy: 92.8 },
      { model: 'LightGBM', mae: 0.063, rmse: 0.149, accuracy: 88.5 },
    ],
    stats: { intersections: 14, records: '2.4M', size: '4.2 GB' },
  },
}

type Year = '2006' | '2014'

export default function ModelEvaluation() {
  const [activeYear, setActiveYear] = useState<Year>('2014')
  const d = DATA[activeYear]
  const bestModel = d.models[0]

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

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Intersections', value: `${d.stats.intersections} nodes` },
          { label: 'Total Records',  value: d.stats.records },
          { label: 'Dataset Size',   value: d.stats.size },
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
            <p className="text-xs text-gray-400 mt-0.5">24-hour SCATS volume pattern</p>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={d.traffic} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
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
              <ReferenceLine y={500} stroke="#e5e7eb" strokeDasharray="4 3"
                label={{ value: 'avg', position: 'right', fontSize: 9, fill: '#d1d5db' }} />
              <Area type="monotone" dataKey="volume" stroke={themeHex.chart} strokeWidth={2.5} fill="url(#trafficGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Model accuracy chart */}
        <div className="bg-white rounded-2xl border border-gray-100 p-6">
          <div className="mb-4">
            <h2 className="font-semibold text-gray-900">Model Accuracy — {activeYear}</h2>
            <p className="text-xs text-gray-400 mt-0.5">Prediction accuracy per model architecture</p>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={d.models} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="barGrad1" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%"   stopColor={themeHex.primary} />
                  <stop offset="100%" stopColor={themeHex.grad} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
              <XAxis dataKey="model" tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
              <YAxis domain={[80, 100]} tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
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
              {d.models.map((m, i) => (
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
        <p className="mt-4 text-xs text-gray-400">
          Best model: <span className="font-semibold text-gray-600">{bestModel.model}</span> —
          Accuracy {bestModel.accuracy}%, MAE {bestModel.mae.toFixed(3)}, RMSE {bestModel.rmse.toFixed(3)}
        </p>
      </div>

    </div>
  )
}
