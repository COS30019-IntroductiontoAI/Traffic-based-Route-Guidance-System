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
    routes = service.get_routes(origin=origin, destination=destination, k=3, algorithm="lightgbm")
    print(json.dumps(routes, indent=2))


if __name__ == "__main__":
    main()
