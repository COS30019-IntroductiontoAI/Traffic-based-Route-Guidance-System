from __future__ import annotations

from backend.route_guidance.types import RouteResult


# Fallback badge mapping for segments that do not have a congestion label yet.
def classify_traffic_level(time_minutes: float) -> str:
    # Map segment duration to the UI traffic badge levels as a safe fallback.
    if time_minutes >= 3.0:
        return "heavy"
    if time_minutes >= 2.0:
        return "moderate"
    return "clear"


# Convert a backend route result into the structure expected by the frontend.
def to_frontend_route(route: RouteResult, rank: int) -> dict[str, object]:
    return {
        "rank": rank,
        "nodes": route.nodes,
        "time": round(route.total_time_minutes, 1),
        "distance": round(route.total_distance_km, 1),
        "segments": [
            {
                "from": segment.from_node,
                "to": segment.to_node,
                "time": round(segment.time_minutes, 1),
                "traffic": segment.traffic_level or classify_traffic_level(segment.time_minutes),
            }
            for segment in route.segments
        ],
    }
