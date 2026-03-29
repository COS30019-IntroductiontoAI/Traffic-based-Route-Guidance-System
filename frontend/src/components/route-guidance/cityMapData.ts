export type AlgorithmId = "lightgbm" | "gru" | "lstm";
export type DataKey = "2006" | "2014";

export interface MapNode {
  id: string;
  x: number;
  y: number;
  lat: number;
  lng: number;
  label: string;
}

export interface MapEdge {
  from: string;
  to: string;
  weight: number;
  distance_km?: number;
}

export interface RouteSegment {
  from: string;
  to: string;
  time: number;
  traffic: "clear" | "moderate" | "heavy";
}

export interface RouteResult {
  rank?: number;
  nodes: string[];
  time: number;
  distance: number;
  segments: RouteSegment[];
}

export interface GraphResponse {
  data?: DataKey;
  nodes: MapNode[];
  edges: MapEdge[];
}

export interface RoutesResponse {
  algorithm: AlgorithmId;
  data: DataKey;
  forecast_timestamp: string | null;
  routes: RouteResult[];
}

export interface RouteGuidanceSelectionOptions {
  data: DataKey;
  available_dates: string[];
  min_date: string | null;
  max_date: string | null;
  times: string[];
  default_date: string | null;
  default_time: string | null;
}

export interface RouteGuidanceConfigResponse {
  supported_data: DataKey[];
  month: number;
  month_label: string;
  defaults: {
    data: DataKey;
    time: string;
    date_by_data: Record<DataKey, string>;
  };
  selection_options: Record<DataKey, RouteGuidanceSelectionOptions>;
}

export const ROUTE_ALGORITHMS: Array<{ id: AlgorithmId; name: string; desc: string }> = [
  { id: "lightgbm", name: "LightGBM", desc: "Gradient boosting (LGBM)" },
  { id: "lstm", name: "LSTM", desc: "Long Short-Term Memory" },
  { id: "gru", name: "GRU", desc: "Gated Recurrent Unit" },
];

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

async function readJson<T>(response: Response): Promise<T> {
  const payload = await response.json();

  if (!response.ok) {
    const message =
      typeof payload === "object" && payload !== null && "error" in payload && typeof payload.error === "string"
        ? payload.error
        : `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return payload as T;
}

function buildApiUrl(path: string, query?: Record<string, string | number>) {
  const url = new URL(`${API_BASE_URL}${path}`);

  if (query) {
    for (const [key, value] of Object.entries(query)) {
      url.searchParams.set(key, String(value));
    }
  }

  return url.toString();
}

export async function fetchGraph(data: DataKey, signal?: AbortSignal): Promise<GraphResponse> {
  const response = await fetch(buildApiUrl("/api/graph", { data }), { signal });
  return readJson<GraphResponse>(response);
}

export async function fetchRouteGuidanceConfig(signal?: AbortSignal): Promise<RouteGuidanceConfigResponse> {
  const response = await fetch(buildApiUrl("/api/route-guidance-config"), { signal });
  return readJson<RouteGuidanceConfigResponse>(response);
}

interface FetchRoutesParams {
  origin: string;
  destination: string;
  k: number;
  algorithm: AlgorithmId;
  data: DataKey;
  date?: string | null;
  time?: string | null;
  signal?: AbortSignal;
}

export async function fetchRoutes({
  origin,
  destination,
  k,
  algorithm,
  data,
  date,
  time,
  signal,
}: FetchRoutesParams): Promise<RoutesResponse> {
  const query: Record<string, string | number> = {
    origin,
    destination,
    k,
    algorithm,
    data,
  };

  if (date) {
    query.date = date;
  }

  if (time) {
    query.time = time;
  }

  const response = await fetch(
    buildApiUrl("/api/routes", query),
    { signal },
  );

  return readJson<RoutesResponse>(response);
}
