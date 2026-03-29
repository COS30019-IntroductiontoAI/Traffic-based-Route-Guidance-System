from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from backend.core.assumptions import DEFAULT_SPEED_LIMIT_KMPH
from backend.route_guidance.heuristic import haversine_distance_km
from backend.route_guidance.travel_time import free_flow_time_minutes
from backend.route_guidance.types import RouteEdge, RouteNode


# Hold the directed graph used by the route search algorithms.
class RouteGraph:
    # Simple adjacency-list graph used by the route engine.
    # Store nodes and outgoing edges in adjacency-list form.
    def __init__(self, nodes: dict[str, RouteNode], adjacency: dict[str, list[RouteEdge]]):
        self.nodes = nodes
        self.adjacency = adjacency

    # Return all outgoing edges for a node.
    def neighbors(self, node_id: str) -> list[RouteEdge]:
        return self.adjacency.get(node_id, [])


# Convert one raw node dictionary into a typed route node.
def _parse_node(raw_node: dict[str, object]) -> RouteNode:
    return RouteNode(
        id=str(raw_node["id"]),
        lat=float(raw_node["lat"]),
        lng=float(raw_node["lng"]),
        label=str(raw_node.get("label", raw_node["id"])),
    )


# Convert one raw edge dictionary into a typed route edge.
def _parse_edge(raw_edge: dict[str, object], nodes: dict[str, RouteNode]) -> RouteEdge:
    from_node = str(raw_edge["from"])
    to_node = str(raw_edge["to"])
    if from_node not in nodes or to_node not in nodes:
        raise KeyError(f"Edge {from_node}->{to_node} references a missing node")

    distance_km = float(raw_edge.get("distance_km", 0.0))
    if distance_km <= 0:
        distance_km = haversine_distance_km(
            nodes[from_node].lat,
            nodes[from_node].lng,
            nodes[to_node].lat,
            nodes[to_node].lng,
        )

    base_time_minutes = float(raw_edge.get("weight", 0.0))
    if base_time_minutes <= 0:
        base_time_minutes = free_flow_time_minutes(distance_km, DEFAULT_SPEED_LIMIT_KMPH)

    metadata = {
        key: value
        for key, value in raw_edge.items()
        if key not in {"from", "to", "weight", "distance_km"}
    }

    return RouteEdge(
        from_node=from_node,
        to_node=to_node,
        distance_km=distance_km,
        base_time_minutes=base_time_minutes,
        metadata=metadata,
    )


# Build a route graph from raw node and edge lists.
def build_graph(nodes_data: list[dict[str, object]], edges_data: list[dict[str, object]]) -> RouteGraph:
    # Build a route graph from raw node/edge dictionaries.
    nodes = {node.id: node for node in (_parse_node(item) for item in nodes_data)}
    adjacency: dict[str, list[RouteEdge]] = defaultdict(list)

    for raw_edge in edges_data:
        edge = _parse_edge(raw_edge, nodes)
        adjacency[edge.from_node].append(edge)

    return RouteGraph(nodes=nodes, adjacency=dict(adjacency))


# Load graph JSON files and convert them into an in-memory route graph.
def load_graph_from_json(nodes_path: str | Path, edges_path: str | Path) -> RouteGraph:
    # Load nodes and edges from JSON files and convert them into a graph.
    nodes_data = json.loads(Path(nodes_path).read_text(encoding="utf-8"))
    edges_data = json.loads(Path(edges_path).read_text(encoding="utf-8"))
    return build_graph(nodes_data, edges_data)
