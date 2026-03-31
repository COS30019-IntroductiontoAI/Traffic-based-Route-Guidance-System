import React, { useState, useEffect, useMemo } from 'react';
import { LoaderCircle, ServerCrash } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

import {
  fetchMetrics,
  type MetricsResponse,
} from '../api_server';

type Year = '2006' | '2014';
type MetricType = 'MAE' | 'RMSE' | 'MAPE';

/* ─── Custom Tooltip Component ────────────────────────────────────────── */
// Component này giúp hiển thị đầy đủ chỉ số bao gồm cả Average khi hover
const CustomTooltip = ({ active, payload, label, avgValue, metricName }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white/95 p-4 border border-gray-200 rounded-xl shadow-xl backdrop-blur-sm">
        <p className="text-sm font-bold text-gray-900 mb-2 border-b pb-1">{label}</p>
        <div className="space-y-1">
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center justify-between gap-8">
              <span className="text-xs font-medium" style={{ color: entry.color }}>
                {entry.name}:
              </span>
              <span className="text-xs font-bold text-gray-700">
                {entry.value.toLocaleString()}
              </span>
            </div>
          ))}
          {/* Dòng hiển thị Average */}
          <div className="flex items-center justify-between gap-8 pt-1 mt-1 border-t border-dashed border-gray-200">
            <span className="text-xs font-medium text-gray-500">
              Overall Average:
            </span>
            <span className="text-xs font-bold text-slate-600">
              {avgValue.toFixed(2)}
            </span>
          </div>
        </div>
      </div>
    );
  }
  return null;
};

export default function ModelEvaluation() {
  const [activeYear, setActiveYear] = useState<Year>('2006');
  const [activeMetric, setActiveMetric] = useState<MetricType>('MAE');
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchMetrics(activeYear)
      .then((m) => setMetrics(m))
      .catch((e) => setError(e instanceof Error ? e.message : 'Error'))
      .finally(() => setLoading(false));
  }, [activeYear]);

  const { chartData, overallAverage } = useMemo(() => {
    if (!metrics?.chart_data) return { chartData: [], overallAverage: 0 };
    const metricKey = activeMetric.toLowerCase() as 'mae' | 'rmse' | 'mape';
    const data = metrics.chart_data[metricKey];

    const rechartsData = data.testIds.map((id, index) => ({
      id,
      lstm: data.lstmData[index],
      gru: data.gruData[index],
      lightgbm: data.lgbmData[index],
    }));

    return { chartData: rechartsData, overallAverage: data.overallAverage };
  }, [metrics, activeMetric]);

  const bestModel = metrics?.models?.length
    ? [...metrics.models].sort((a, b) => a.mape - b.mape)[0]
    : null;

  return (
    <div className="p-8 space-y-6 h-full overflow-auto bg-gray-50/50 font-sans">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Model Evaluation Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">Evaluate ML model performance using Recharts.</p>
      </div>

      {/* Tabs */}
      <div className="inline-flex bg-gray-200/60 p-1 rounded-xl gap-1">
        {(['2006', '2014'] as const).map((y) => (
          <button
            key={y}
            onClick={() => setActiveYear(y)}
            className={`px-6 py-2 rounded-lg text-sm font-semibold transition-all ${
              activeYear === y ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Data Year: {y}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-32 text-slate-400 gap-3">
          <LoaderCircle className="w-6 h-6 animate-spin text-blue-500" />
          <span className="text-sm font-medium">Processing metrics data...</span>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { label: 'Total Intersections', value: `${metrics?.stats.intersections} nodes` },
              { label: 'Total Records', value: metrics?.stats.records },
              { label: 'Dataset Date Range', value: metrics?.stats.date_range },
            ].map((s) => (
              <div key={s.label} className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
                <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">{s.label}</p>
                <p className="text-xl font-bold text-gray-900 mt-1">{s.value}</p>
              </div>
            ))}
          </div>

          {/* Main Chart Card */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-lg font-bold text-gray-900">Detailed Models Comparison - {activeYear}</h2>
                <p className="text-xs text-gray-400 mt-1">Grouped Bar Chart with Overall Average Line Overlay</p>
              </div>
              <div className="flex bg-gray-100 p-1 rounded-lg gap-1">
                {(['MAE', 'RMSE', 'MAPE'] as const).map(m => (
                  <button
                    key={m}
                    onClick={() => setActiveMetric(m)}
                    className={`px-4 py-1.5 rounded-md text-xs font-bold transition-all ${
                      activeMetric === m ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>

            <div className="h-[450px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }} barGap={8}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis 
                    dataKey="id" 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fill: '#94a3b8', fontSize: 12, fontWeight: 500 }} 
                    dy={10}
                  />
                  <YAxis 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fill: '#94a3b8', fontSize: 12 }} 
                  />
                  
                  {/* Tooltip Tùy Chỉnh để thấy Average */}
                  <Tooltip 
                    content={<CustomTooltip avgValue={overallAverage} metricName={activeMetric} />}
                    cursor={{ fill: '#f1f5f9', opacity: 0.4 }} 
                  />
                  
                  <Legend 
                    verticalAlign="top" 
                    align="center" 
                    iconType="circle" 
                    iconSize={8}
                    wrapperStyle={{ paddingBottom: '30px', fontSize: '12px', fontWeight: 'bold' }}
                  />

                  {/* Đường trung bình rõ nét hơn */}
                  <ReferenceLine 
                    y={overallAverage} 
                    stroke="#64748b" 
                    strokeDasharray="6 6" 
                    strokeWidth={2}
                    label={{ 
                      position: 'top', 
                      // value: `Overall Average ${activeMetric} (${overallAverage.toFixed(2)})`,
                      fill: '#475569',
                      fontSize: 11,
                      fontWeight: 700,
                      offset: 10
                    }} 
                  />

                  <Bar dataKey="lstm" name="LSTM" fill="#8b5cf6" radius={[4, 4, 0, 0]} barSize={20} />
                  <Bar dataKey="gru" name="GRU" fill="#fbbf24" radius={[4, 4, 0, 0]} barSize={20} />
                  <Bar dataKey="lightgbm" name="LIGHTGBM" fill="#ef4444" radius={[4, 4, 0, 0]} barSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Footer */}
            {bestModel && (
              <div className="mt-8 pt-5 border-t border-gray-100 flex items-center gap-4">
                <span className="text-[10px] px-3 py-1 rounded-full font-black bg-emerald-50 text-emerald-600 border border-emerald-200 uppercase tracking-tighter">
                  Best Overall Model
                </span>
                <p className="text-sm text-gray-600 font-medium">
                  <span className="font-bold text-gray-900">{bestModel.model}</span> achieves{' '}
                  MAE: <span className="text-gray-900 font-bold">{bestModel.mae.toFixed(3)}</span>, 
                  RMSE: <span className="text-gray-900 font-bold">{bestModel.rmse.toFixed(3)}</span>, 
                  MAPE: <span className="text-gray-900 font-bold">{bestModel.mape.toFixed(3)}</span> <br/>
                  (<strong>Note:</strong> Based on the datasets from test_metrics_full_{activeYear}.csv and the avarage of 10 test cases)
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}