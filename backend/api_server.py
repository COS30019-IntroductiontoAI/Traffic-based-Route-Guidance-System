from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from backend.core.config import get_predictions_path
from backend.services.route_service import RouteService, SUPPORTED_ALGORITHMS, SUPPORTED_DATA_KEYS


HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8000))
ROUTE_SERVICE = RouteService.from_scats_graph()
if ROUTE_SERVICE.model_inference is not None:
    ROUTE_SERVICE.model_inference.predict_site_flow_map()


# Send a JSON response with CORS headers for the frontend.
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


# Compute summary metrics from the prepared predictions file.
def _compute_metrics(data_key: str) -> dict:
    """Compute real MAE / RMSE / Accuracy from the predictions CSV."""
    import pandas as pd
    import numpy as np

    path = get_predictions_path(data_key)
    df = pd.read_csv(path, parse_dates=["datetime"])

    models_info = [
        ("LightGBM", "predicted_lightgbm"),
        ("LSTM",     "predicted_lstm"),
        ("GRU",      "predicted_gru"),
    ]

    results = []
    for name, col in models_info:
        if col not in df.columns:
            continue
        actual = df["actual"].values
        pred   = df[col].values
        mae    = float(np.mean(np.abs(actual - pred)))
        rmse   = float(np.sqrt(np.mean((actual - pred) ** 2)))
        nonzero = actual != 0
        if nonzero.any():
            mape = float(np.mean(np.abs((actual[nonzero] - pred[nonzero]) / actual[nonzero])) * 100)
        else:
            mape = 100.0
        accuracy = max(0.0, 100.0 - mape)
        results.append({
            "model":    name,
            "mae":      round(mae, 3),
            "rmse":     round(rmse, 3),
            "mape":     round(mape, 2),
        })

    # Sort by accuracy descending so the best model is first
    results.sort(key=lambda x: x["mape"])

    # Dataset-level stats
    n_sites = int(df["scats_number"].nunique())
    n_records = len(df)
    dt_min = str(df["datetime"].min().date())
    dt_max = str(df["datetime"].max().date())

    # Load detailed metrics from CSV
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    metrics_path = os.path.join(base_dir, "src", "results", "test_results", f"test_metrics_full_{data_key}.csv")
    
    try:
        if not os.path.exists(metrics_path):
            raise FileNotFoundError
    except FileNotFoundError:
        metrics_path = os.path.join(base_dir, "frontend", "data", "csv", f"test_metrics_full_{data_key}.csv")
        
    detailed_metrics = []
    chart_data = None
    if os.path.exists(metrics_path):
        df_metrics = pd.read_csv(metrics_path)
        # Convert dataframe to a list of dicts, keeping necessary columns
        if not df_metrics.empty:
            # fillna(0) to ensure JSON compliant output
            detailed_metrics = df_metrics.fillna(0).to_dict(orient="records")

            chart_data = {
                "mae": { "lstmData": [], "gruData": [], "lgbmData": [], "testIds": [], "overallAverage": 0.0 },
                "rmse": { "lstmData": [], "gruData": [], "lgbmData": [], "testIds": [], "overallAverage": 0.0 },
                "mape": { "lstmData": [], "gruData": [], "lgbmData": [], "testIds": [], "overallAverage": 0.0 }
            }
            
            unique_test_ids = sorted([str(x) for x in df_metrics["test_id"].unique()])
            
            for metric in ["mae", "rmse", "mape"]:
                lst_data = []
                gru_data = []
                lgbm_data = []
                
                for tid in unique_test_ids:
                    sub = df_metrics[df_metrics["test_id"].astype(str) == tid]
                    
                    lstm = sub[sub["model"].str.upper() == "LSTM"][metric].values
                    lst_data.append(float(lstm[0]) if len(lstm) else 0.0)
                    
                    gru = sub[sub["model"].str.upper() == "GRU"][metric].values
                    gru_data.append(float(gru[0]) if len(gru) else 0.0)
                    
                    lgbm = sub[sub["model"].str.upper() == "LIGHTGBM"][metric].values
                    lgbm_data.append(float(lgbm[0]) if len(lgbm) else 0.0)
                
                all_vals = lst_data + gru_data + lgbm_data
                avg = sum(all_vals) / len(all_vals) if all_vals else 0.0
                
                chart_data[metric] = {
                    "testIds": unique_test_ids,
                    "lstmData": lst_data,
                    "gruData": gru_data,
                    "lgbmData": lgbm_data,
                    "overallAverage": avg
                }

    return {
        "models": results,
        "detailed_metrics": detailed_metrics,
        "chart_data": chart_data,
        "stats": {
            "intersections": n_sites,
            "records": f"{n_records:,}",
            "date_range": f"{dt_min} – {dt_max}",
        },
    }


# Build an hourly traffic profile for dashboard-style charts.
def _compute_traffic_profile(data_key: str) -> list[dict]:
    """Return average hourly traffic volume aggregated across all sites and days."""
    import pandas as pd

    path = get_predictions_path(data_key)
    df = pd.read_csv(path, parse_dates=["datetime"])

    if "hour" not in df.columns:
        df["hour"] = df["datetime"].dt.hour

    profile = (
        df.groupby("hour")["actual"]
        .mean()
        .reset_index()
        .rename(columns={"hour": "hour", "actual": "volume"})
    )

    return [
        {"time": f"{int(row.hour):02d}:00", "volume": round(float(row.volume), 1)}
        for row in profile.itertuples(index=False)
        if int(row.hour) % 3 == 0  # return every 3 hours for chart readability
    ]


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

        if parsed.path == "/api/health":
            _json_response(self, 200, {"status": "ok"})
            return

        if parsed.path == "/api/graph":
            params = parse_qs(parsed.query)
            data_key = params.get("data", ["2014"])[0].strip().lower()
            if data_key not in SUPPORTED_DATA_KEYS:
                _json_response(self, 400, {"error": f"data must be one of {sorted(SUPPORTED_DATA_KEYS)}"})
                return
            _json_response(
                self,
                200,
                ROUTE_SERVICE.get_graph_payload(data_key),
            )
            return

        if parsed.path == "/api/route-guidance-config":
            try:
                payload = ROUTE_SERVICE.get_route_guidance_config()
            except Exception as exc:  # noqa: BLE001
                _json_response(self, 500, {"error": str(exc)})
                return
            _json_response(self, 200, payload)
            return

        if parsed.path == "/api/timestamps":
            params = parse_qs(parsed.query)
            data_key = params.get("data", ["2014"])[0].strip().lower()
            if data_key not in SUPPORTED_DATA_KEYS:
                _json_response(self, 400, {"error": f"data must be one of {sorted(SUPPORTED_DATA_KEYS)}"})
                return
            try:
                payload = ROUTE_SERVICE.get_time_options(data_key)
            except Exception as exc:  # noqa: BLE001
                _json_response(self, 500, {"error": str(exc)})
                return
            _json_response(self, 200, payload)
            return

        if parsed.path == "/api/metrics":
            params   = parse_qs(parsed.query)
            data_key = params.get("data", ["2014"])[0].strip().lower()
            if data_key not in SUPPORTED_DATA_KEYS:
                _json_response(self, 400, {"error": f"data must be one of {sorted(SUPPORTED_DATA_KEYS)}"})
                return
            try:
                result = _compute_metrics(data_key)
            except Exception as exc:  # noqa: BLE001
                _json_response(self, 500, {"error": str(exc)})
                return
            _json_response(self, 200, result)
            return

        if parsed.path == "/api/traffic-profile":
            params   = parse_qs(parsed.query)
            data_key = params.get("data", ["2014"])[0].strip().lower()
            if data_key not in SUPPORTED_DATA_KEYS:
                _json_response(self, 400, {"error": f"data must be one of {sorted(SUPPORTED_DATA_KEYS)}"})
                return
            try:
                profile = _compute_traffic_profile(data_key)
            except Exception as exc:  # noqa: BLE001
                _json_response(self, 500, {"error": str(exc)})
                return
            _json_response(self, 200, {"profile": profile})
            return

        if parsed.path == "/api/routes":
            params = parse_qs(parsed.query)
            origin = params.get("origin", [""])[0]
            destination = params.get("destination", [""])[0]
            algorithm = params.get("algorithm", ["lightgbm"])[0]
            data_key = params.get("data", ["2014"])[0]
            timestamp = params.get("timestamp", [""])[0].strip() or None
            date_value = params.get("date", [""])[0].strip() or None
            time_of_day = params.get("time", [""])[0].strip() or None
            if timestamp is None and date_value and time_of_day:
                timestamp = f"{date_value}T{time_of_day}:00"
            print(f"[API] Route search: origin={origin}, destination={destination}, algorithm={algorithm}, data={data_key}, date={date_value}, time={time_of_day}, k={params.get('k', ['5'])[0]}")
            try:
                k = int(params.get("k", ["5"])[0])
            except ValueError:
                _json_response(self, 400, {"error": "k must be an integer"})
                return

            if not origin or not destination:
                _json_response(self, 400, {"error": "origin and destination are required"})
                return
            if algorithm.strip().lower() not in SUPPORTED_ALGORITHMS:
                _json_response(self, 400, {"error": f"algorithm must be one of {sorted(SUPPORTED_ALGORITHMS)}"})
                return
            if data_key.strip().lower() not in SUPPORTED_DATA_KEYS:
                _json_response(self, 400, {"error": f"data must be one of {sorted(SUPPORTED_DATA_KEYS)}"})
                return

            try:
                result = ROUTE_SERVICE.get_routes(
                    origin=origin,
                    destination=destination,
                    k=k,
                    algorithm=algorithm,
                    data_key=data_key,
                    target_datetime=timestamp,
                )
            except ValueError as exc:
                _json_response(self, 400, {"error": str(exc)})
                return
            except Exception as exc:  # noqa: BLE001
                _json_response(self, 500, {"error": str(exc)})
                return

            _json_response(self, 200, result)
            return


        if parsed.path == "/api/storytelling":
            params = parse_qs(parsed.query)
            file_name = params.get("file", [""])[0]
            
            if not file_name:
                _json_response(self, 400, {"error": "Missing file parameter"})
                return
                
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(base_dir, "src", "data", "storytelling_vis", file_name)
            
            try:
                import json
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                _json_response(self, 200, data)
            except FileNotFoundError:
                try:
                    fallback_file_path = os.path.join(base_dir, "frontend", "data", "json", file_name)
                    with open(fallback_file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    _json_response(self, 200, data)
                except FileNotFoundError:
                    _json_response(self, 404, {"error": f"File not found: {file_name}"})
            except Exception as exc:  # noqa: BLE001
                _json_response(self, 500, {"error": str(exc)})
            return


        _json_response(self, 404, {"error": "Not found"})


# Start the local backend HTTP server.
def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), RouteGuidanceHandler)
    print(f"Backend API running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()