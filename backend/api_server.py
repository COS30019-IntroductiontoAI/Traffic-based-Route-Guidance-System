from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import pandas as pd

from backend.core.config import MAX_ROUTE_K, TRAFFIC_PROFILE_HOUR_STEP, get_predictions_path
from backend.services.route_service import RouteService, SUPPORTED_ALGORITHMS, SUPPORTED_DATA_KEYS

# Use environment variables for host and port to ensure compatibility with Render.
HOST = os.environ.get("HOST", "0.0.0.0")
PORT_STR = os.environ.get("PORT", "8000")

# Handle cases where PORT might be set to a full URL or have extra formatting
if ":" in PORT_STR:
    # Extract port number from URLs like 'http://localhost:8000'
    PORT_STR = PORT_STR.split(":")[-1]

try:
    PORT = int(PORT_STR.strip())
except (ValueError, AttributeError):
    PORT = 8000
LOGGER = logging.getLogger("backend.api_server")


# Represent one controlled API error that should be shown to the client.
class ApiError(Exception):
    def __init__(self, message: str, status_code: int, category: str):
        super().__init__(message)
        self.status_code = status_code
        self.category = category


# Mark a client-side request problem such as invalid params.
class ApiValidationError(ApiError):
    def __init__(self, message: str):
        super().__init__(message, status_code=400, category="validation")


# Mark a missing-file or data-read problem from prepared artifacts.
class ApiDataError(ApiError):
    def __init__(self, message: str):
        super().__init__(message, status_code=500, category="data")


# Mark an unknown endpoint without treating it as an internal failure.
class ApiNotFoundError(ApiError):
    def __init__(self, message: str = "Not found"):
        super().__init__(message, status_code=404, category="not_found")


# Build the shared route service lazily so import itself stays cheap and predictable.
@lru_cache(maxsize=1)
def get_route_service() -> RouteService:
    # We create the service only when the first request needs it.
    # This avoids expensive startup work during import and makes tests safer to import.
    return RouteService.from_scats_graph()


# Send one JSON response with CORS headers for the frontend.
def _json_response(handler: BaseHTTPRequestHandler, status_code: int, payload: dict[str, object]) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)


# Return one consistent error payload instead of leaking raw internal exceptions.
def _error_response(handler: BaseHTTPRequestHandler, error: ApiError) -> None:
    _json_response(
        handler,
        error.status_code,
        {
            "error": str(error),
            "category": error.category,
        },
    )


# Convert one raw exception into an API-safe error category.
def _wrap_exception(exc: Exception) -> ApiError:
    if isinstance(exc, ApiError):
        return exc
    if isinstance(exc, FileNotFoundError):
        return ApiDataError(str(exc))
    if isinstance(exc, ValueError):
        return ApiValidationError(str(exc))
    return ApiError("Internal server error", status_code=500, category="internal")


# Read one required query value and strip surrounding whitespace.
def _get_query_value(params: dict[str, list[str]], name: str, default: str = "") -> str:
    return params.get(name, [default])[0].strip()


# Validate a required SCATS node id.
def _parse_node_id(params: dict[str, list[str]], name: str) -> str:
    value = _get_query_value(params, name)
    if not value:
        raise ApiValidationError(f"{name} is required")
    if not value.isdigit():
        raise ApiValidationError(f"{name} must be a numeric SCATS ID")
    return value


# Validate one integer query parameter with a minimum and maximum.
def _parse_positive_int(
    params: dict[str, list[str]],
    field_name: str,
    *,
    minimum: int,
    maximum: int | None = None,
    default: int,
) -> int:
    raw_value = _get_query_value(params, field_name, str(default))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ApiValidationError(f"{field_name} must be an integer") from exc

    if value < minimum:
        raise ApiValidationError(f"{field_name} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise ApiValidationError(f"{field_name} must be at most {maximum}")
    return value


# Normalize one query option and reject unsupported values early.
def _normalize_choice(params: dict[str, list[str]], field_name: str, allowed: set[str], default: str) -> str:
    value = _get_query_value(params, field_name, default).lower()
    if value not in allowed:
        raise ApiValidationError(f"{field_name} must be one of {sorted(allowed)}")
    return value


# Resolve the optional timestamp from either a direct ISO string or date/time pair.
def _parse_timestamp(params: dict[str, list[str]]) -> str | None:
    timestamp = _get_query_value(params, "timestamp") or None
    if timestamp is not None:
        return timestamp

    date_value = _get_query_value(params, "date") or None
    time_of_day = _get_query_value(params, "time") or None
    if date_value and time_of_day:
        return f"{date_value}T{time_of_day}:00"
    return None


# Compute summary metrics from the prepared predictions file.
def _compute_metrics(data_key: str) -> dict[str, object]:
    path = get_predictions_path(data_key)
    if not path.exists():
        raise ApiDataError(f"Predictions file not found for dataset '{data_key}'")

    df = pd.read_csv(path, parse_dates=["datetime"])
    results: list[dict[str, Any]] = []

    models_info = [
        ("LightGBM", "predicted_lightgbm"),
        ("LSTM", "predicted_lstm"),
        ("GRU", "predicted_gru"),
    ]

    # These metrics are intentionally computed from the prepared predictions CSV.
    # The backend should report model quality, not trigger another prediction pipeline run.
    for model_name, prediction_column in models_info:
        if prediction_column not in df.columns:
            continue

        actual = df["actual"].to_numpy(dtype=float)
        predicted = df[prediction_column].to_numpy(dtype=float)
        mae = float((abs(actual - predicted)).mean())
        rmse = float((((actual - predicted) ** 2).mean()) ** 0.5)
        nonzero = actual != 0
        mape = float((abs((actual[nonzero] - predicted[nonzero]) / actual[nonzero])).mean() * 100) if nonzero.any() else 100.0

        results.append(
            {
                "model": model_name,
                "mae": round(mae, 3),
                "rmse": round(rmse, 3),
                "mape": round(mape, 2),
            }
        )

    results.sort(key=lambda item: item["mape"])

    n_sites = int(df["scats_number"].nunique())
    n_records = len(df)
    dt_min = str(df["datetime"].min().date())
    dt_max = str(df["datetime"].max().date())

    base_dir = Path(__file__).resolve().parents[1]
    primary_metrics_path = base_dir / "src" / "results" / "test_results" / f"test_metrics_full_{data_key}.csv"
    fallback_metrics_path = base_dir / "frontend" / "data" / "csv" / f"test_metrics_full_{data_key}.csv"
    metrics_path = primary_metrics_path if primary_metrics_path.exists() else fallback_metrics_path

    detailed_metrics: list[dict[str, object]] = []
    chart_data: dict[str, object] | None = None

    if metrics_path.exists():
        df_metrics = pd.read_csv(metrics_path)
        if not df_metrics.empty:
            detailed_metrics = df_metrics.fillna(0).to_dict(orient="records")

            # We pivot once here because the frontend wants one series per model and per metric.
            # Doing that upfront avoids repeated filtering loops over the same table.
            pivot = (
                df_metrics.assign(test_id=df_metrics["test_id"].astype(str), model=df_metrics["model"].str.upper())
                .pivot_table(index="test_id", columns="model", values=["mae", "rmse", "mape"], aggfunc="first")
                .fillna(0.0)
            )

            test_ids = sorted(pivot.index.tolist())
            chart_data = {}
            for metric in ("mae", "rmse", "mape"):
                lstm_data = [float(pivot.get((metric, "LSTM"), pd.Series(index=test_ids, dtype=float)).get(test_id, 0.0)) for test_id in test_ids]
                gru_data = [float(pivot.get((metric, "GRU"), pd.Series(index=test_ids, dtype=float)).get(test_id, 0.0)) for test_id in test_ids]
                lgbm_data = [float(pivot.get((metric, "LIGHTGBM"), pd.Series(index=test_ids, dtype=float)).get(test_id, 0.0)) for test_id in test_ids]
                all_values = lstm_data + gru_data + lgbm_data

                chart_data[metric] = {
                    "testIds": test_ids,
                    "lstmData": lstm_data,
                    "gruData": gru_data,
                    "lgbmData": lgbm_data,
                    "overallAverage": (sum(all_values) / len(all_values)) if all_values else 0.0,
                }

    return {
        "models": results,
        "detailed_metrics": detailed_metrics,
        "chart_data": chart_data,
        "stats": {
            "intersections": n_sites,
            "records": f"{n_records:,}",
            "date_range": f"{dt_min} - {dt_max}",
        },
    }


# Build an hourly traffic profile for dashboard-style charts.
def _compute_traffic_profile(data_key: str) -> list[dict[str, object]]:
    path = get_predictions_path(data_key)
    if not path.exists():
        raise ApiDataError(f"Predictions file not found for dataset '{data_key}'")

    df = pd.read_csv(path, parse_dates=["datetime"])
    if "hour" not in df.columns:
        df["hour"] = df["datetime"].dt.hour

    # The dashboard profile is meant to show a simple day-shape summary for the selected dataset,
    # so we average by hour across all sites and all days rather than exposing raw time series.
    profile = (
        df.groupby("hour", observed=False)["actual"]
        .mean()
        .reset_index()
        .rename(columns={"actual": "volume"})
    )

    # Sample every few hours intentionally so the dashboard remains readable instead of noisy.
    return [
        {"time": f"{int(row.hour):02d}:00", "volume": round(float(row.volume), 1)}
        for row in profile.itertuples(index=False)
        if int(row.hour) % TRAFFIC_PROFILE_HOUR_STEP == 0
    ]


# Read one storytelling JSON file from the backend-first, frontend-second search path.
def _load_storytelling_payload(file_name: str) -> dict[str, object]:
    if not file_name:
        raise ApiValidationError("file is required")

    base_dir = Path(__file__).resolve().parents[1]
    candidate_paths = [
        base_dir / "src" / "data" / "storytelling_vis" / file_name,
        base_dir / "frontend" / "data" / "json" / file_name,
    ]

    for candidate_path in candidate_paths:
        if candidate_path.exists():
            with candidate_path.open("r", encoding="utf-8") as file_handle:
                return json.load(file_handle)

    raise ApiDataError(f"File not found: {file_name}")


# Expose the small local HTTP API used by the frontend.
class RouteGuidanceHandler(BaseHTTPRequestHandler):
    # Minimal local backend API for frontend route-guidance integration.

    # Handle CORS preflight requests from the frontend.
    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # Route every GET request to the matching backend endpoint.
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        try:
            # Keep simple read-only endpoints first because they are the cheapest and easiest to reason about.
            if parsed.path == "/api/health":
                _json_response(self, 200, {"status": "ok"})
                return

            if parsed.path == "/api/graph":
                data_key = _normalize_choice(params, "data", SUPPORTED_DATA_KEYS, "2014")
                _json_response(self, 200, get_route_service().get_graph_payload(data_key))
                return

            if parsed.path == "/api/route-guidance-config":
                _json_response(self, 200, get_route_service().get_route_guidance_config())
                return

            if parsed.path == "/api/timestamps":
                data_key = _normalize_choice(params, "data", SUPPORTED_DATA_KEYS, "2014")
                _json_response(self, 200, get_route_service().get_time_options(data_key))
                return

            if parsed.path == "/api/metrics":
                data_key = _normalize_choice(params, "data", SUPPORTED_DATA_KEYS, "2014")
                _json_response(self, 200, _compute_metrics(data_key))
                return

            if parsed.path == "/api/traffic-profile":
                data_key = _normalize_choice(params, "data", SUPPORTED_DATA_KEYS, "2014")
                _json_response(self, 200, {"profile": _compute_traffic_profile(data_key)})
                return

            if parsed.path == "/api/routes":
                # Validate the route inputs before touching the route engine so user errors fail fast
                # and never propagate as algorithm/runtime failures deeper in the stack.
                origin = _parse_node_id(params, "origin")
                destination = _parse_node_id(params, "destination")
                algorithm = _normalize_choice(params, "algorithm", SUPPORTED_ALGORITHMS, "lightgbm")
                data_key = _normalize_choice(params, "data", SUPPORTED_DATA_KEYS, "2014")
                k = _parse_positive_int(params, "k", minimum=1, maximum=MAX_ROUTE_K, default=5)
                timestamp = _parse_timestamp(params)

                # The log keeps enough context to reproduce the route request later without dumping internals.
                LOGGER.info(
                    "Route search request origin=%s destination=%s algorithm=%s data=%s timestamp=%s k=%s",
                    origin,
                    destination,
                    algorithm,
                    data_key,
                    timestamp,
                    k,
                )
                result = get_route_service().get_routes(
                    origin=origin,
                    destination=destination,
                    k=k,
                    algorithm=algorithm,
                    data_key=data_key,
                    target_datetime=timestamp,
                )
                _json_response(self, 200, result)
                return

            if parsed.path == "/api/storytelling":
                file_name = _get_query_value(params, "file")
                _json_response(self, 200, _load_storytelling_payload(file_name))
                return

            raise ApiNotFoundError()

        except Exception as exc:  # noqa: BLE001
            error = _wrap_exception(exc)
            # Internal failures should be logged with stack traces.
            # Client-side validation failures should stay clean and readable.
            if error.status_code >= 500:
                LOGGER.exception("API request failed path=%s", parsed.path, exc_info=exc)
            else:
                LOGGER.warning("API request rejected path=%s error=%s", parsed.path, error)
            _error_response(self, error)


# Start the local backend HTTP server.
def main() -> None:
    # Configure logging here so imports stay side-effect light and tests can override logging if needed.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    
    try:
        LOGGER.info("Starting backend API server with HOST=%s PORT=%s", HOST, PORT)
        
        # Validate that required configuration can be loaded before starting the server
        from backend.core.config import (
            BACKEND_CONFIG_PATH,
            GENERATED_DIR,
            PREDICTIONS_DIR,
        )
        
        if not BACKEND_CONFIG_PATH.exists():
            LOGGER.error("Configuration file not found: %s", BACKEND_CONFIG_PATH)
            raise FileNotFoundError(f"Backend config not found at {BACKEND_CONFIG_PATH}")
        
        LOGGER.info("Config file found at %s", BACKEND_CONFIG_PATH)
        
        # Initialize route service (this is expensive, so we do it once during startup validation)
        LOGGER.info("Initializing route service and loading graphs...")
        service = get_route_service()
        LOGGER.info("Route service initialized successfully with graphs: %s", list(service.graphs_by_data.keys()))
        
        # Create the server
        server = ThreadingHTTPServer((HOST, PORT), RouteGuidanceHandler)
        LOGGER.info("Backend API running at http://%s:%s", HOST, PORT)
        server.serve_forever()
        
    except Exception as exc:
        LOGGER.exception("Failed to start backend API server: %s", exc)
        raise


if __name__ == "__main__":
    main()
