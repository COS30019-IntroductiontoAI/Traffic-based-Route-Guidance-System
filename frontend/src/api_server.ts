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

// Determine the API base URL with multiple fallback strategies
function getApiBaseUrl(): string {
  // First try environment variable (set during build)
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '');
  }
  
  // For GitHub Pages production, use the Render backend
  if (typeof window !== 'undefined' && window.location.hostname.includes('github.io')) {
    return 'https://traffic-based-route-guidance-system.onrender.com';
  }
  
  // Default: for local development, use localhost
  return 'http://127.0.0.1:8000';
}

const API_BASE = getApiBaseUrl()

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
