from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from backend.core.assumptions import DEFAULT_SPEED_LIMIT_KMPH
from backend.route_guidance.types import RouteNode


# Compute the great-circle distance between two latitude/longitude pairs.
def haversine_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    earth_radius_km = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
    )
    return 2 * earth_radius_km * asin(sqrt(a))


# Estimate straight-line travel time for the A* heuristic.
def straight_line_time_minutes(
    origin: RouteNode,
    destination: RouteNode,
    speed_kmph: float = DEFAULT_SPEED_LIMIT_KMPH,
) -> float:
    if speed_kmph <= 0:
        return 0.0
    distance_km = haversine_distance_km(origin.lat, origin.lng, destination.lat, destination.lng)
    return (distance_km / speed_kmph) * 60.0
