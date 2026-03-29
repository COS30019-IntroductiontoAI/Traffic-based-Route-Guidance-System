from __future__ import annotations

from backend.core.assumptions import (
    DEFAULT_CONGESTION_SCALE,
    DEFAULT_INTERSECTION_DELAY_SECONDS,
    DEFAULT_SPEED_LIMIT_KMPH,
    MAX_CONGESTION_MULTIPLIER,
)


# Convert distance into a free-flow travel time estimate.
def free_flow_time_minutes(distance_km: float, speed_kmph: float = DEFAULT_SPEED_LIMIT_KMPH) -> float:
    if speed_kmph <= 0:
        raise ValueError("speed_kmph must be positive")
    return (distance_km / speed_kmph) * 60.0


# Turn predicted flow into a bounded travel-time multiplier.
def congestion_multiplier(
    predicted_flow: float | None,
    reference_flow: float | None = None,
    scale: float = DEFAULT_CONGESTION_SCALE,
) -> float:
    # Use a simple normalized ratio when no per-site reference flow is available.
    if predicted_flow is None or predicted_flow <= 0:
        return 1.0

    if reference_flow is None or reference_flow <= 0:
        normalized_flow = predicted_flow / 200.0
    else:
        # Exaggerate the impact of high predictions and remove the hard 1.0 bottleneck 
        # so that slight differences between ML models produce different route choices
        normalized_flow = (predicted_flow / reference_flow) ** 1.5

    return min(1.0 + normalized_flow * scale, MAX_CONGESTION_MULTIPLIER)


# Map predicted congestion into the badge levels shown in the frontend.
def classify_congestion_level(
    predicted_flow: float | None,
    reference_flow: float | None = None,
) -> str:
    if predicted_flow is None or predicted_flow <= 0:
        return "clear"

    if reference_flow is None or reference_flow <= 0:
        normalized_flow = min(predicted_flow / 200.0, 1.0)
    else:
        normalized_flow = min(predicted_flow / reference_flow, 1.0)

    if normalized_flow >= 0.85:
        return "heavy"
    if normalized_flow >= 0.55:
        return "moderate"
    return "clear"


# Estimate one segment time from distance, congestion, and intersection delay.
def estimate_edge_travel_time_minutes(
    distance_km: float,
    predicted_flow: float | None = None,
    reference_flow: float | None = None,
    speed_kmph: float = DEFAULT_SPEED_LIMIT_KMPH,
    include_intersection_delay: bool = True,
    intersection_delay_seconds: float = DEFAULT_INTERSECTION_DELAY_SECONDS,
) -> float:
    base_minutes = free_flow_time_minutes(distance_km, speed_kmph)
    travel_minutes = base_minutes * congestion_multiplier(predicted_flow, reference_flow)

    if include_intersection_delay:
        travel_minutes += intersection_delay_seconds / 60.0

    return travel_minutes
