from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from typing import Callable

from backend.route_guidance.graph_builder import RouteGraph
from backend.route_guidance.heuristic import straight_line_time_minutes
from backend.route_guidance.types import RouteEdge, RouteResult, RouteSegment


# Store one A* frontier entry with its current priority.
@dataclass(slots=True)
class _FrontierState:
    priority: float
    node_id: str

    # Keep the heap ordered by priority.
    def __lt__(self, other: "_FrontierState") -> bool:
        return self.priority < other.priority


# Rebuild the final node path from the A* parent pointers.
def _reconstruct_path(came_from: dict[str, str | None], destination: str) -> list[str]:
    path = [destination]
    current = destination

    while came_from[current] is not None:
        current = came_from[current]  # type: ignore[assignment]
        path.append(current)

    path.reverse()
    return path


# Resolve one edge from a path pair without assuming the graph is always perfectly consistent.
def _find_edge(graph: RouteGraph, from_node: str, to_node: str) -> RouteEdge | None:
    for edge in graph.neighbors(from_node):
        if edge.to_node == to_node:
            return edge
    return None


# Find the single best route between two nodes using A* search.
def find_route(
    graph: RouteGraph,
    origin: str,
    destination: str,
    edge_cost_lookup: Callable[[RouteEdge], float],
) -> RouteResult | None:
    # Run A* on the current graph using the supplied edge cost function.
    if origin not in graph.nodes or destination not in graph.nodes:
        return None

    frontier: list[_FrontierState] = []
    heappush(frontier, _FrontierState(priority=0.0, node_id=origin))

    came_from: dict[str, str | None] = {origin: None}
    cost_so_far: dict[str, float] = {origin: 0.0}

    while frontier:
        current = heappop(frontier).node_id
        if current == destination:
            break

        # A* combines the exact cost so far with a straight-line optimistic heuristic.
        # That keeps the route search focused without changing the true path cost definition.
        for edge in graph.neighbors(current):
            new_cost = cost_so_far[current] + float(edge_cost_lookup(edge))
            if edge.to_node not in cost_so_far or new_cost < cost_so_far[edge.to_node]:
                cost_so_far[edge.to_node] = new_cost
                heuristic = straight_line_time_minutes(graph.nodes[edge.to_node], graph.nodes[destination])
                heappush(frontier, _FrontierState(priority=new_cost + heuristic, node_id=edge.to_node))
                came_from[edge.to_node] = current

    if destination not in cost_so_far:
        return None

    path_nodes = _reconstruct_path(came_from, destination)
    segments: list[RouteSegment] = []
    total_distance_km = 0.0

    # Rebuild segment details after the search so the search loop itself stays lightweight.
    for from_node, to_node in zip(path_nodes, path_nodes[1:]):
        edge = _find_edge(graph, from_node, to_node)
        if edge is None:
            return None
        edge_minutes = float(edge_cost_lookup(edge))
        segments.append(RouteSegment(from_node=from_node, to_node=to_node, time_minutes=edge_minutes))
        total_distance_km += edge.distance_km

    return RouteResult(
        nodes=path_nodes,
        total_time_minutes=cost_so_far[destination],
        total_distance_km=total_distance_km,
        segments=segments,
    )
