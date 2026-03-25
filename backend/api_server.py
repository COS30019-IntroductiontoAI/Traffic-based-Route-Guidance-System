from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from backend.core.config import SCATS_EDGES_PATH, SCATS_NODES_PATH
from backend.services.route_service import RouteService, SUPPORTED_ALGORITHMS, SUPPORTED_DATA_KEYS


HOST = "127.0.0.1"
PORT = 8000
ROUTE_SERVICE = RouteService.from_scats_graph()
if ROUTE_SERVICE.model_inference is not None:
    ROUTE_SERVICE.model_inference.predict_site_flow_map()


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


class RouteGuidanceHandler(BaseHTTPRequestHandler):
    # Minimal local backend API for frontend route-guidance integration.
    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)

        if parsed.path == "/api/health":
            _json_response(self, 200, {"status": "ok"})
            return

        if parsed.path == "/api/graph":
            _json_response(
                self,
                200,
                {
                    "nodes": json.loads(SCATS_NODES_PATH.read_text(encoding="utf-8")),
                    "edges": json.loads(SCATS_EDGES_PATH.read_text(encoding="utf-8")),
                },
            )
            return

        if parsed.path == "/api/routes":
            params = parse_qs(parsed.query)
            origin = params.get("origin", [""])[0]
            destination = params.get("destination", [""])[0]
            algorithm = params.get("algorithm", ["lightgbm"])[0]
            data_key = params.get("data", ["2014"])[0]
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
                )
            except Exception as exc:  # noqa: BLE001
                _json_response(self, 500, {"error": str(exc)})
                return

            _json_response(self, 200, result)
            return

        _json_response(self, 404, {"error": "Not found"})


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), RouteGuidanceHandler)
    print(f"Backend API running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
