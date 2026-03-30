export interface ModelMetric {
  model: string
  mae: number
  rmse: number
  mape: number
}

export interface DetailedMetric {
  test_id: string
  model: string
  mae: number
  rmse: number
  mape: number
  n_samples?: number
}

export interface MetricsStats {
  intersections: number
  records: string
  date_range: string
}

export interface ChartDataPayload {
  testIds: string[]
  lstmData: number[]
  gruData: number[]
  lgbmData: number[]
  overallAverage: number
}

export interface MetricsResponse {
  models: ModelMetric[]
  stats: MetricsStats
  detailed_metrics?: DetailedMetric[]
  chart_data?: {
    mae: ChartDataPayload
    rmse: ChartDataPayload
    mape: ChartDataPayload
  }
}

export interface TrafficPoint {
  time: string
  volume: number
}

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '')

export async function fetchMetrics(year: string): Promise<MetricsResponse> {
  const res = await fetch(`${API_BASE}/api/metrics?data=${year}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json() as Promise<MetricsResponse>
}

export async function fetchTrafficProfile(year: string): Promise<TrafficPoint[]> {
  const res = await fetch(`${API_BASE}/api/traffic-profile?data=${year}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const data = await res.json() as { profile: TrafficPoint[] }
  return data.profile
}
