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
        # Returning an empty list instead of raising keeps the search code simple and defensive.
        return self.adjacency.get(node_id, [])


# Convert one raw node dictionary into a typed route node.
def _parse_node(raw_node: dict[str, object]) -> RouteNode:
    # The graph JSON already has the shape the frontend uses, so this is mostly a typed conversion step.
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
        # Recover missing geometry from node coordinates so graph JSON stays tolerant of partial exports.
        distance_km = haversine_distance_km(
            nodes[from_node].lat,
            nodes[from_node].lng,
            nodes[to_node].lat,
            nodes[to_node].lng,
        )

    base_time_minutes = float(raw_edge.get("weight", 0.0))
    if base_time_minutes <= 0:
        # Rebuild a free-flow baseline so routing can still run even if only distance is present.
        base_time_minutes = free_flow_time_minutes(distance_km, DEFAULT_SPEED_LIMIT_KMPH)

    metadata = {
        key: value
        for key, value in raw_edge.items()
        if key not in {"from", "to", "weight", "distance_km"}
    }
    # We preserve extra metadata so future frontend features can use it without changing graph parsing again.

    return RouteEdge(
        from_node=from_node,
        to_node=to_node,
        distance_km=distance_km,
        base_time_minutes=base_time_minutes,
        metadata=metadata,
    )


# Build a route graph from raw node and edge lists.
def build_graph(nodes_data: list[dict[str, object]], edges_data: list[dict[str, object]]) -> RouteGraph:
    # This keeps graph JSON parsing isolated so the search layer only deals with typed nodes and edges.
    nodes = {node.id: node for node in (_parse_node(item) for item in nodes_data)}
    adjacency: dict[str, list[RouteEdge]] = defaultdict(list)

    for raw_edge in edges_data:
        edge = _parse_edge(raw_edge, nodes)
        adjacency[edge.from_node].append(edge)

    # We materialize a plain dict here so the rest of the backend sees a stable read-only-style structure
    # instead of depending on defaultdict behavior.
    return RouteGraph(nodes=nodes, adjacency=dict(adjacency))


# Load graph JSON files and convert them into an in-memory route graph.
def load_graph_from_json(nodes_path: str | Path, edges_path: str | Path) -> RouteGraph:
    # JSON files are the boundary between preprocessing/generation and runtime route search.
    nodes_path = Path(nodes_path)
    edges_path = Path(edges_path)
    
    # Validate that the files exist
    if not nodes_path.exists():
        raise FileNotFoundError(f"Graph nodes file not found at {nodes_path}")
    if not edges_path.exists():
        raise FileNotFoundError(f"Graph edges file not found at {edges_path}")
    
    try:
        nodes_data = json.loads(nodes_path.read_text(encoding="utf-8"))
        edges_data = json.loads(edges_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse graph JSON files: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to load graph files: {e}") from e
    
    return build_graph(nodes_data, edges_data)
