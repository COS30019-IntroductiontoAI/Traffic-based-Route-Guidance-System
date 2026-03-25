from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RouteNode:
    id: str
    lat: float
    lng: float
    label: str | None = None


@dataclass(slots=True)
class RouteEdge:
    from_node: str
    to_node: str
    distance_km: float
    base_time_minutes: float
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class RouteSegment:
    from_node: str
    to_node: str
    time_minutes: float


@dataclass(slots=True)
class RouteResult:
    nodes: list[str]
    total_time_minutes: float
    total_distance_km: float
    segments: list[RouteSegment]
