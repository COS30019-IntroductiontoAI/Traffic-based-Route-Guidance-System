from __future__ import annotations

from dataclasses import dataclass, field


# Represent one intersection node in the route graph.
@dataclass(slots=True)
class RouteNode:
    # We keep both id and display label because the frontend needs a machine id and a user-facing name.
    id: str
    lat: float
    lng: float
    label: str | None = None


# Represent one directed road segment between two nodes.
@dataclass(slots=True)
class RouteEdge:
    # base_time_minutes is the free-flow estimate before model-based congestion is applied.
    from_node: str
    to_node: str
    distance_km: float
    base_time_minutes: float
    metadata: dict[str, object] = field(default_factory=dict)


# Represent one traversed segment inside a computed route.
@dataclass(slots=True)
class RouteSegment:
    # traffic_level is attached later so search logic stays separate from presentation logic.
    from_node: str
    to_node: str
    time_minutes: float
    traffic_level: str = "clear"


# Represent one complete route returned to the frontend.
@dataclass(slots=True)
class RouteResult:
    # nodes stores the ordered path.
    # segments stores the richer per-edge details used by the frontend panels.
    nodes: list[str]
    total_time_minutes: float
    total_distance_km: float
    segments: list[RouteSegment]
