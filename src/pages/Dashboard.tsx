import { Database, Cpu, TrendingUp, Database as DbIcon, Navigation, Activity, CheckCircle, Clock } from 'lucide-react'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import StatCard from '../components/StatCard'
import { useApp } from '../App'
import { themeHex } from '../theme'

const trafficData = [
  { time: '00:00', volume: 120 }, { time: '03:00', volume: 80 },  { time: '06:00', volume: 200 },
  { time: '09:00', volume: 780 }, { time: '12:00', volume: 650 }, { time: '15:00', volume: 820 },
  { time: '18:00', volume: 900 }, { time: '21:00', volume: 480 },
]

const modelData = [
  { model: 'LSTM', accuracy: 94.2 },
  { model: 'GRU',  accuracy: 92.8 },
  { model: 'RF',   accuracy: 88.5 },
  { model: 'SVR',  accuracy: 84.1 },
]

const recentActivity = [
  { icon: <CheckCircle size={13} className="text-emerald-500" />, text: 'SCATS Volume Data synced successfully', time: '2m ago',  color: 'bg-emerald-50' },
  { icon: <Activity    size={13} className="text-indigo-500"  />, text: 'LSTM-v4 model retrained on new data',   time: '2h ago',  color: 'bg-indigo-50'  },
  { icon: <CheckCircle size={13} className="text-emerald-500" />, text: 'Road Network Graph updated (14K nodes)', time: '1d ago',  color: 'bg-emerald-50' },
  { icon: <Clock       size={13} className="text-amber-500"   />, text: 'Weather Correlation dataset pending sync', time: '—',    color: 'bg-amber-50'   },
]

export default function Dashboard() {
  const { navigate, toast } = useApp()

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Traffic-Based Route Guidance System</h1>
          <p className="text-sm text-gray-400 mt-1">System operational. 14 intersections optimized.</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-50 border border-emerald-100 rounded-xl">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-xs font-semibold text-emerald-700">Live</span>
        </div>
      </div>

      {/* Stats */}
      <div className="flex gap-4">
        <StatCard label="Dataset Status"      value="8.4 GB Synced"  sub="14 SCATS nodes active"      icon={<Database    size={20} />} accent="#6366f1" />
        <StatCard label="Model Status"        value="LSTM-v4 Active" sub="Last trained 2h ago"         icon={<Cpu         size={20} />} accent="#8b5cf6" />
        <StatCard label="Prediction Accuracy" value="94.2%"          sub="MAE: 0.042 | RMSE: 0.118"   icon={<TrendingUp  size={20} />} accent="#06b6d4" />
      </div>

      {/* Action buttons */}
      <div className="flex gap-3">
        <button onClick={() => { navigate('data-processing');    toast('Navigating to Data Processing', 'info') }}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-white text-sm font-semibold active:scale-95 transition-all shadow-sm"
          style={{ backgroundColor: themeHex.primary }}>
          <DbIcon size={15} /> Load Dataset
        </button>
        <button onClick={() => { navigate('route-guidance');     toast('Navigating to Route Guidance', 'info') }}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-white text-sm font-semibold active:scale-95 transition-all shadow-sm"
          style={{ background: `linear-gradient(to right, ${themeHex.primary}, ${themeHex.grad})` }}>
          <Navigation size={15} /> Find Routes
        </button>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-2 gap-4">
        {/* Traffic Flow */}
        <div className="bg-white rounded-2xl border border-gray-100 p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="font-semibold text-gray-900">Traffic Flow</h2>
              <p className="text-xs text-gray-400 mt-0.5">24-hour volume pattern</p>
            </div>
            <span className="text-xs text-indigo-500 font-semibold bg-indigo-50 px-2 py-0.5 rounded-lg"
              style={{ color: themeHex.primary, backgroundColor: themeHex.primary50 }}>Today</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={trafficData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
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
              <ReferenceLine y={500} stroke="#e5e7eb" strokeDasharray="4 3" label={{ value: 'avg', position: 'right', fontSize: 9, fill: '#d1d5db' }} />
              <Area type="monotone" dataKey="volume" stroke={themeHex.chart} strokeWidth={2.5} fill="url(#trafficGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Model Comparison */}
        <div className="bg-white rounded-2xl border border-gray-100 p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="font-semibold text-gray-900">Model Comparison</h2>
              <p className="text-xs text-gray-400 mt-0.5">Accuracy across architectures</p>
            </div>
            {/* Removed Details button as model training page is deleted */}
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={modelData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
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

      {/* Recent Activity */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6">
        <h2 className="font-semibold text-gray-900 mb-4">Recent Activity</h2>
        <div className="space-y-2">
          {recentActivity.map((item, i) => (
            <div key={i} className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-gray-50 transition-colors">
              <div className={`w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0 ${item.color}`}>
                {item.icon}
              </div>
              <p className="text-sm text-gray-600 flex-1">{item.text}</p>
              <span className="text-xs text-gray-400 flex-shrink-0 font-mono">{item.time}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
