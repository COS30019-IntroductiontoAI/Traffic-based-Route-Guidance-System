from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush

from backend.route_guidance.graph_builder import RouteGraph
from backend.route_guidance.types import RouteResult, RouteSegment


# Store one candidate path inside the top-k search frontier.
@dataclass(slots=True)
class _PathState:
    total_cost: float
    nodes: tuple[str, ...]

    # Keep the heap ordered by the current total path cost.
    def __lt__(self, other: "_PathState") -> bool:
        return self.total_cost < other.total_cost


# Convert a node path into a detailed route with distances and segment times.
def _build_route_result(
    graph: RouteGraph,
    path_nodes: tuple[str, ...],
    edge_cost_lookup,
) -> RouteResult:
    segments: list[RouteSegment] = []
    total_distance_km = 0.0
    total_time_minutes = 0.0

    for from_node, to_node in zip(path_nodes, path_nodes[1:]):
        edge = next(edge for edge in graph.neighbors(from_node) if edge.to_node == to_node)
        edge_minutes = float(edge_cost_lookup(edge))
        total_time_minutes += edge_minutes
        total_distance_km += edge.distance_km
        segments.append(RouteSegment(from_node=from_node, to_node=to_node, time_minutes=edge_minutes))

    return RouteResult(
        nodes=list(path_nodes),
        total_time_minutes=total_time_minutes,
        total_distance_km=total_distance_km,
        segments=segments,
    )


# Return up to k distinct simple routes ordered by total path cost.
def find_top_k_routes(
    graph: RouteGraph,
    origin: str,
    destination: str,
    edge_cost_lookup,
    k: int = 5,
) -> list[RouteResult]:
    if k <= 0:
        return []
    if origin not in graph.nodes or destination not in graph.nodes:
        return []

    frontier: list[_PathState] = [_PathState(total_cost=0.0, nodes=(origin,))]
    seen_paths: set[tuple[str, ...]] = set()
    routes: list[RouteResult] = []

    while frontier and len(routes) < k:
        state = heappop(frontier)
        current = state.nodes[-1]

        if current == destination:
            if state.nodes in seen_paths:
                continue
            seen_paths.add(state.nodes)
            routes.append(_build_route_result(graph, state.nodes, edge_cost_lookup))
            continue

        visited = set(state.nodes)
        for edge in graph.neighbors(current):
            if edge.to_node in visited:
                continue

            edge_cost = float(edge_cost_lookup(edge))
            if edge_cost == float("inf"):
                continue

            heappush(
                frontier,
                _PathState(
                    total_cost=state.total_cost + edge_cost,
                    nodes=state.nodes + (edge.to_node,),
                ),
            )

    return routes
