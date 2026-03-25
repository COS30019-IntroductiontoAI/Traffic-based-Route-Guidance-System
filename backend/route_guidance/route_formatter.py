from __future__ import annotations

from backend.route_guidance.types import RouteResult


def classify_traffic_level(time_minutes: float) -> str:
    # Map a segment time to the UI traffic badge levels.
    if time_minutes >= 3.0:
        return "heavy"
    if time_minutes >= 2.0:
        return "moderate"
    return "clear"


def to_frontend_route(route: RouteResult, rank: int) -> dict[str, object]:
    # Convert a backend route result into the structure Nam's UI already expects.
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
                "traffic": classify_traffic_level(segment.time_minutes),
            }
            for segment in route.segments
        ],
    }
