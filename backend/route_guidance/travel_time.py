from __future__ import annotations

from backend.core.assumptions import (
    DEFAULT_CONGESTION_SCALE,
    DEFAULT_INTERSECTION_DELAY_SECONDS,
    DEFAULT_SPEED_LIMIT_KMPH,
    MAX_CONGESTION_MULTIPLIER,
)


def free_flow_time_minutes(distance_km: float, speed_kmph: float = DEFAULT_SPEED_LIMIT_KMPH) -> float:
    # Convert distance to free-flow travel time.
    if speed_kmph <= 0:
        raise ValueError("speed_kmph must be positive")
    return (distance_km / speed_kmph) * 60.0


def congestion_multiplier(
    predicted_flow: float | None,
    reference_flow: float | None = None,
    scale: float = DEFAULT_CONGESTION_SCALE,
) -> float:
    # Return a bounded multiplier based on the predicted flow intensity.
    if predicted_flow is None or predicted_flow <= 0:
        return 1.0

    if reference_flow is None or reference_flow <= 0:
        normalized_flow = predicted_flow / 200.0
    else:
        # Exaggerate the impact of high predictions and remove the hard 1.0 bottleneck 
        # so that slight differences between ML models produce different route choices
        normalized_flow = (predicted_flow / reference_flow) ** 1.5

    return min(1.0 + normalized_flow * scale, MAX_CONGESTION_MULTIPLIER)


def estimate_edge_travel_time_minutes(
    distance_km: float,
    predicted_flow: float | None = None,
    reference_flow: float | None = None,
    speed_kmph: float = DEFAULT_SPEED_LIMIT_KMPH,
    include_intersection_delay: bool = True,
    intersection_delay_seconds: float = DEFAULT_INTERSECTION_DELAY_SECONDS,
) -> float:
    # Estimate an edge travel time from distance plus optional congestion.
    base_minutes = free_flow_time_minutes(distance_km, speed_kmph)
    travel_minutes = base_minutes * congestion_multiplier(predicted_flow, reference_flow)

    if include_intersection_delay:
        travel_minutes += intersection_delay_seconds / 60.0

    return travel_minutes
