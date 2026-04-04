from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from typing import Callable

from backend.route_guidance.graph_builder import RouteGraph
from backend.route_guidance.types import RouteEdge, RouteResult, RouteSegment


# Store one candidate complete path inside the Yen-style candidate heap.
@dataclass(slots=True)
class _PathCandidate:
    total_cost: float
    nodes: tuple[str, ...]

    # Keep the heap ordered by the current total path cost.
    def __lt__(self, other: "_PathCandidate") -> bool:
        return self.total_cost < other.total_cost


# Resolve one directed edge from a path pair without crashing on bad graph state.
def _find_edge(graph: RouteGraph, from_node: str, to_node: str) -> RouteEdge | None:
    for edge in graph.neighbors(from_node):
        if edge.to_node == to_node:
            return edge
    return None


# Convert a node path into a detailed route with distances and segment times.
def _build_route_result(
    graph: RouteGraph,
    path_nodes: tuple[str, ...],
    edge_cost_lookup: Callable[[RouteEdge], float],
) -> RouteResult | None:
    segments: list[RouteSegment] = []
    total_distance_km = 0.0
    total_time_minutes = 0.0

    for from_node, to_node in zip(path_nodes, path_nodes[1:]):
        edge = _find_edge(graph, from_node, to_node)
        if edge is None:
            return None
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


# Compute the total path cost again from the chosen node sequence.
def _path_cost(
    graph: RouteGraph,
    path_nodes: tuple[str, ...],
    edge_cost_lookup: Callable[[RouteEdge], float],
) -> float | None:
    # Yen-style search needs the cost of a complete candidate path after it is assembled.
    total_cost = 0.0
    for from_node, to_node in zip(path_nodes, path_nodes[1:]):
        edge = _find_edge(graph, from_node, to_node)
        if edge is None:
            return None
        total_cost += float(edge_cost_lookup(edge))
    return total_cost


# Find one shortest path while temporarily blocking specific nodes or edges.
def _find_shortest_path(
    graph: RouteGraph,
    origin: str,
    destination: str,
    edge_cost_lookup: Callable[[RouteEdge], float],
    *,
    blocked_nodes: frozenset[str] = frozenset(),
    blocked_edges: frozenset[tuple[str, str]] = frozenset(),
) -> tuple[str, ...] | None:
    if origin in blocked_nodes or destination in blocked_nodes:
        return None

    # This is a lightweight shortest-path helper used only inside the top-k routine.
    # It accepts temporary node/edge bans so we can generate route deviations safely.
    frontier: list[tuple[float, str]] = [(0.0, origin)]
    came_from: dict[str, str | None] = {origin: None}
    cost_so_far: dict[str, float] = {origin: 0.0}

    while frontier:
        current_cost, current = heappop(frontier)
        if current == destination:
            break
        if current_cost > cost_so_far[current]:
            continue

        for edge in graph.neighbors(current):
            if edge.to_node in blocked_nodes:
                continue
            if (edge.from_node, edge.to_node) in blocked_edges:
                continue

            edge_cost = float(edge_cost_lookup(edge))
            if edge_cost == float("inf"):
                continue

            new_cost = current_cost + edge_cost
            if edge.to_node not in cost_so_far or new_cost < cost_so_far[edge.to_node]:
                cost_so_far[edge.to_node] = new_cost
                came_from[edge.to_node] = current
                heappush(frontier, (new_cost, edge.to_node))

    if destination not in came_from:
        return None

    path: list[str] = [destination]
    current = destination
    while came_from[current] is not None:
        current = came_from[current]  # type: ignore[assignment]
        path.append(current)
    path.reverse()
    return tuple(path)


# Return up to k distinct simple routes ordered by total path cost.
def find_top_k_routes(
    graph: RouteGraph,
    origin: str,
    destination: str,
    edge_cost_lookup: Callable[[RouteEdge], float],
    k: int = 5,
) -> list[RouteResult]:
    if k <= 0:
        return []
    if origin not in graph.nodes or destination not in graph.nodes:
        return []

    # Use a Yen-style loop so we enumerate alternative routes from shortest-path deviations
    # instead of exploring the entire simple-path search space blindly.
    # This makes top-k behavior much more controlled than the earlier frontier-of-whole-paths approach.
    first_path = _find_shortest_path(graph, origin, destination, edge_cost_lookup)
    if first_path is None:
        return []

    shortest_paths: list[tuple[str, ...]] = [first_path]
    candidate_heap: list[_PathCandidate] = []
    candidate_paths: set[tuple[str, ...]] = set()

    while len(shortest_paths) < k:
        previous_best = shortest_paths[-1]

        for spur_index in range(len(previous_best) - 1):
            root_path = previous_best[: spur_index + 1]
            spur_node = root_path[-1]

            # Remove only the next edge for paths that share the same root.
            # This is the key Yen idea that forces the next candidate to deviate after the shared prefix.
            removed_edges = {
                (path[spur_index], path[spur_index + 1])
                for path in shortest_paths
                if len(path) > spur_index + 1 and path[: spur_index + 1] == root_path
            }
            blocked_nodes = frozenset(root_path[:-1])

            spur_path = _find_shortest_path(
                graph,
                spur_node,
                destination,
                edge_cost_lookup,
                blocked_nodes=blocked_nodes,
                blocked_edges=frozenset(removed_edges),
            )
            if spur_path is None:
                continue

            candidate_path = root_path[:-1] + spur_path
            if candidate_path in candidate_paths or candidate_path in shortest_paths:
                continue

            candidate_cost = _path_cost(graph, candidate_path, edge_cost_lookup)
            if candidate_cost is None:
                continue

            candidate_paths.add(candidate_path)
            heappush(candidate_heap, _PathCandidate(total_cost=candidate_cost, nodes=candidate_path))

        if not candidate_heap:
            break

        # The next accepted path is the cheapest remaining valid deviation.
        next_candidate = heappop(candidate_heap)
        candidate_paths.discard(next_candidate.nodes)
        shortest_paths.append(next_candidate.nodes)

    routes: list[RouteResult] = []
    for path_nodes in shortest_paths[:k]:
        route = _build_route_result(graph, path_nodes, edge_cost_lookup)
        if route is not None:
            routes.append(route)
    return routes
