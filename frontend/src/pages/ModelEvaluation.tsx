import React, { useState, useEffect, useMemo } from 'react'
import { LoaderCircle, ServerCrash } from 'lucide-react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  Filler,
  type ChartOptions,
  type ChartData
} from 'chart.js'
import { Bar } from 'react-chartjs-2'

// Đăng ký các module cần thiết của Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  Filler
)

import {
  fetchMetrics,
  fetchTrafficProfile,
  type MetricsResponse,
  type TrafficPoint
} from '../api_server'

/* ─── Component ──────────────────────────────────────────────────────────── */

type Year = '2006' | '2014'
type MetricType = 'MAE' | 'RMSE' | 'MAPE'

export default function ModelEvaluation() {
  const [activeYear, setActiveYear] = useState<Year>('2006')
  const [activeMetric, setActiveMetric] = useState<MetricType>('MAE')

  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [traffic, setTraffic] = useState<TrafficPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)

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

  /* ─── Data Processing for Chart.js ─────────────────────────────────────── */

  const { chartData, testIds, overallAverage } = useMemo(() => {
    if (!metrics?.chart_data) return { chartData: null, testIds: [], overallAverage: 0 }

    const metricKey = activeMetric.toLowerCase() as 'mae' | 'rmse' | 'mape'
    const data = metrics.chart_data[metricKey]

    return {
      testIds: data.testIds,
      chartData: { lstmData: data.lstmData, gruData: data.gruData, lgbmData: data.lgbmData },
      overallAverage: data.overallAverage
    }
  }, [metrics, activeMetric])

  /* ─── Chart Configurations ─────────────────────────────────────────────── */

  const mainChartData: ChartData<any> = {
    labels: testIds,
    datasets: [
      {
        type: 'line',
        label: `Overall Average ${activeMetric} (${overallAverage.toFixed(2)})`,
        data: testIds.map(() => overallAverage),
        borderColor: '#64748b',
        backgroundColor: '#64748b',
        borderWidth: 2,
        borderDash: [7, 7],
        pointRadius: 0,
        tension: 0,
        order: 1,
      },
      {
        type: 'bar',
        label: 'LSTM',
        data: chartData?.lstmData || [],
        backgroundColor: '#8b5cf6',
        hoverBackgroundColor: '#7e22ce',
        borderRadius: 4,
        order: 2
      },
      {
        type: 'bar',
        label: 'GRU',
        data: chartData?.gruData || [],
        backgroundColor: '#fbbf24',
        hoverBackgroundColor: '#facc15',
        borderRadius: 4,
        order: 2
      },
      {
        type: 'bar',
        label: 'LIGHTGBM',
        data: chartData?.lgbmData || [],
        backgroundColor: '#ef4444',
        hoverBackgroundColor: '#dc2626',
        borderRadius: 4,
        order: 2
      },
    ]
  }

  const mainChartOptions: ChartOptions<any> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { position: 'top', labels: { usePointStyle: true, boxWidth: 8 } },
      tooltip: {
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        titleColor: '#1f2937', bodyColor: '#4b5563', borderColor: '#e5e7eb', borderWidth: 1, padding: 12
      }
    },
    scales: {
      x: { grid: { display: false } },
      y: { grid: { color: '#f3f4f6' }, beginAtZero: true }
    }
  }

  const bestModel = metrics?.models?.length
    ? [...metrics.models].sort((a, b) => b.mape - a.mape)[0]
    : null;

  return (
    <div className="p-8 space-y-6 animate-fade-up h-full overflow-auto bg-gray-50/50">

      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Model Evaluation Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">
          Evaluate ML model performance using Chart.js on SCATS traffic datasets.
        </p>
      </div>

      {/* Year tabs */}
      <div className="inline-flex bg-gray-200/60 p-1 rounded-xl gap-1">
        {(['2006', '2014'] as const).map((y) => (
          <button
            key={y}
            onClick={() => setActiveYear(y)}
            className={`px-6 py-2 rounded-lg text-sm font-semibold transition-all ${activeYear === y ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'
              }`}
          >
            Data Year: {y}
          </button>
        ))}
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center py-32 text-slate-400 gap-3">
          <LoaderCircle className="w-6 h-6 animate-spin text-blue-500" />
          <span className="text-sm font-medium">Processing metrics data...</span>
        </div>
      )}

      {!loading && error && (
        <div className="flex flex-col items-center justify-center py-20 text-center gap-3 bg-white rounded-2xl border border-red-100">
          <ServerCrash className="w-10 h-10 text-red-400" />
          <p className="text-sm font-semibold text-slate-700">Could not load evaluation data</p>
          <p className="text-xs text-slate-500">{error}</p>
        </div>
      )}

      {!loading && !error && metrics && (
        <div className="space-y-6">
          {/* Cột thống kê nhanh */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { label: 'Total Intersections', value: `${metrics.stats.intersections} nodes` },
              { label: 'Total Records', value: metrics.stats.records },
              { label: 'Dataset Date Range', value: metrics.stats.date_range },
            ].map((s) => (
              <div key={s.label} className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
                <p className="text-xs text-gray-400 font-medium uppercase tracking-wider">{s.label}</p>
                <p className="text-xl font-bold text-gray-900 mt-1.5">{s.value}</p>
              </div>
            ))}
          </div>

          {/* Biểu đồ chính kết hợp */}
          <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-bold text-gray-900">
                  Detailed Models Comparison - {activeYear}
                </h2>
                <p className="text-xs text-gray-400 mt-1">Grouped Bar Chart with Overall Average Line Overlay</p>
              </div>
              <div className="flex bg-gray-100 p-1 rounded-lg gap-1">
                {(['MAE', 'RMSE', 'MAPE'] as const).map(m => (
                  <button
                    key={m}
                    onClick={() => setActiveMetric(m)}
                    className={`px-4 py-1.5 rounded-md text-xs font-bold transition-all ${activeMetric === m ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                      }`}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>

            <div className="h-[450px] w-full mt-4">
              {testIds.length > 0 ? (
                <Bar 
                  data={mainChartData} 
                  options={mainChartOptions} 
                  plugins={[{
                    id: 'extendLine',
                    afterDatasetsDraw(chart) {
                      const meta = chart.getDatasetMeta(0);
                      if (!meta || meta.type !== 'line' || meta.data.length === 0) return;
                      
                      const { ctx, chartArea: { left, right } } = chart;
                      const firstPoint = meta.data[0];
                      const lastPoint = meta.data[meta.data.length - 1];
                      
                      ctx.save();
                      ctx.lineWidth = 2;
                      ctx.strokeStyle = '#64748b';
                      ctx.setLineDash([7, 7]);
                      
                      ctx.beginPath();
                      ctx.moveTo(left, firstPoint.y);
                      ctx.lineTo(firstPoint.x, firstPoint.y);
                      ctx.stroke();
                      
                      ctx.beginPath();
                      ctx.moveTo(lastPoint.x, lastPoint.y);
                      ctx.lineTo(right, lastPoint.y);
                      ctx.stroke();
                      
                      ctx.restore();
                    }
                  }]}
                />
              ) : (
                <div className="h-full flex items-center justify-center text-sm text-gray-400 border-2 border-dashed border-gray-100 rounded-xl">
                  No detailed metrics found for {activeYear}.
                </div>
              )}
            </div>

            {bestModel && (
              <div className="mt-8 pt-4 border-t border-gray-50 flex flex-wrap items-center gap-3">
                <span className="text-xs px-3 py-1.5 rounded-full font-bold bg-emerald-50 text-emerald-600 border border-emerald-100">
                  Best Overall Model
                </span>
                <p className="text-sm text-gray-600">
                  <span className="font-bold text-gray-900">{bestModel.model}</span> achieves{' '}
                  MAE: <span className="font-semibold text-gray-800">{bestModel.mae.toFixed(3)}</span>,
                  RMSE: <span className="font-semibold text-gray-800">{bestModel.rmse.toFixed(3)}</span>,
                  MAPE: <span className="font-semibold text-gray-800">{bestModel.mape.toFixed(3)}</span> <br />
                  (Note: Based on test_metrics_full_{activeYear}.csv)
                </p>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  )
}