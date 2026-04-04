from __future__ import annotations

import json

from backend.services.route_service import RouteService


# Run a small local smoke test against the route service.
def main() -> None:
    # Small local smoke-test entrypoint for the backend route engine.
    service = RouteService.from_scats_graph()

    # Sample pair from the generated SCATS graph.
    origin = "970"
    destination = "4043"
    # This script intentionally stays tiny: it is only meant to prove the route stack can run end-to-end.
    # It is not part of the frontend flow and should stay safe to run from the command line.
    routes = service.get_routes(origin=origin, destination=destination, k=3, algorithm="lightgbm")
    print(json.dumps(routes, indent=2))


if __name__ == "__main__":
    main()
