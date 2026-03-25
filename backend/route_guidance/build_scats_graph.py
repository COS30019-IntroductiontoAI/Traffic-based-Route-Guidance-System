from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from backend.route_guidance.heuristic import haversine_distance_km


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRAFFIC_PATH = PROJECT_ROOT / "data" / "processed" / "processed_traffic.csv"
SITE_LISTING_PATH = PROJECT_ROOT / "data" / "processed" / "SCATSSiteListingSpreadsheet_VicRoads_clean.csv"
OUTPUT_DIR = PROJECT_ROOT / "backend" / "generated"
NODES_OUTPUT = OUTPUT_DIR / "scats_nodes.json"
EDGES_OUTPUT = OUTPUT_DIR / "scats_edges.json"


@dataclass(slots=True)
class SiteRecord:
    scats_number: int
    lat: float
    lng: float
    road_name: str
    label: str


def load_site_records() -> list[SiteRecord]:
    # Build one site-level record per SCATS site from the processed dataset.
    traffic_df = pd.read_csv(TRAFFIC_PATH)
    listing_df = pd.read_csv(SITE_LISTING_PATH).rename(columns={"site_number": "scats_number"})

    site_df = (
        traffic_df.groupby("scats_number")
        .agg(
            nb_latitude=("nb_latitude", "mean"),
            nb_longitude=("nb_longitude", "mean"),
            road_name=("road_name", lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0]),
        )
        .reset_index()
    )

    site_df = site_df.merge(
        listing_df[["scats_number", "location_description"]],
        on="scats_number",
        how="left",
    )

    records: list[SiteRecord] = []
    for row in site_df.itertuples(index=False):
        label = row.location_description if pd.notna(row.location_description) else row.road_name
        records.append(
            SiteRecord(
                scats_number=int(row.scats_number),
                lat=float(row.nb_latitude),
                lng=float(row.nb_longitude),
                road_name=str(row.road_name),
                label=str(label),
            )
        )
    return records


def build_distance_table(records: list[SiteRecord]) -> dict[tuple[int, int], float]:
    # Precompute pairwise site distances in kilometers.
    distances: dict[tuple[int, int], float] = {}
    for i, left in enumerate(records):
        for right in records[i + 1 :]:
            distance_km = haversine_distance_km(left.lat, left.lng, right.lat, right.lng)
            distances[(left.scats_number, right.scats_number)] = distance_km
            distances[(right.scats_number, left.scats_number)] = distance_km
    return distances


def connect_nearest_neighbors(
    records: list[SiteRecord],
    distances: dict[tuple[int, int], float],
    neighbors_per_site: int = 3,
) -> set[tuple[int, int]]:
    # Create an undirected candidate graph by linking each site to nearby sites.
    undirected_edges: set[tuple[int, int]] = set()

    for site in records:
        candidates = sorted(
            (
                (distances[(site.scats_number, other.scats_number)], other.scats_number)
                for other in records
                if other.scats_number != site.scats_number
            ),
            key=lambda item: item[0],
        )

        for _, neighbor in candidates[:neighbors_per_site]:
            edge = tuple(sorted((site.scats_number, neighbor)))
            undirected_edges.add(edge)

    return undirected_edges


def connect_same_road_sites(
    records: list[SiteRecord],
    distances: dict[tuple[int, int], float],
) -> set[tuple[int, int]]:
    # Add extra edges between sites that appear to lie on the same corridor.
    undirected_edges: set[tuple[int, int]] = set()
    by_road: dict[str, list[SiteRecord]] = {}

    for site in records:
        by_road.setdefault(site.road_name, []).append(site)

    for road_sites in by_road.values():
        if len(road_sites) < 2:
            continue

        for site in road_sites:
            same_road_neighbors = sorted(
                (
                    (distances[(site.scats_number, other.scats_number)], other.scats_number)
                    for other in road_sites
                    if other.scats_number != site.scats_number
                ),
                key=lambda item: item[0],
            )
            if same_road_neighbors:
                edge = tuple(sorted((site.scats_number, same_road_neighbors[0][1])))
                undirected_edges.add(edge)

    return undirected_edges


def connected_components(records: list[SiteRecord], edges: set[tuple[int, int]]) -> list[set[int]]:
    # Return connected components for the current undirected graph.
    adjacency: dict[int, set[int]] = {record.scats_number: set() for record in records}
    for left, right in edges:
        adjacency[left].add(right)
        adjacency[right].add(left)

    remaining = set(adjacency)
    components: list[set[int]] = []

    while remaining:
        start = remaining.pop()
        stack = [start]
        component = {start}

        while stack:
            node = stack.pop()
            for neighbor in adjacency[node]:
                if neighbor not in component:
                    component.add(neighbor)
                    remaining.discard(neighbor)
                    stack.append(neighbor)

        components.append(component)

    return components


def connect_components(
    records: list[SiteRecord],
    distances: dict[tuple[int, int], float],
    edges: set[tuple[int, int]],
) -> set[tuple[int, int]]:
    # Ensure the graph is connected by joining the closest disconnected components.
    site_lookup = {record.scats_number: record for record in records}
    components = connected_components(records, edges)

    while len(components) > 1:
        first = components[0]
        best_pair: tuple[int, int] | None = None
        best_distance = float("inf")

        for other_component in components[1:]:
            for left in first:
                for right in other_component:
                    distance_km = distances[(left, right)]
                    if distance_km < best_distance:
                        best_distance = distance_km
                        best_pair = tuple(sorted((left, right)))

        if best_pair is None:
            break

        edges.add(best_pair)
        components = connected_components(records, edges)

    # Prevent linter warnings about the lookup remaining unused if we later extend the graph metadata.
    _ = site_lookup
    return edges


def export_scats_graph() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    # Generate a frontend-compatible SCATS graph and save it to JSON files.
    records = load_site_records()
    distances = build_distance_table(records)

    undirected_edges = connect_nearest_neighbors(records, distances, neighbors_per_site=3)
    undirected_edges |= connect_same_road_sites(records, distances)
    undirected_edges = connect_components(records, distances, undirected_edges)

    nodes = [
        {
            "id": str(record.scats_number),
            "lat": record.lat,
            "lng": record.lng,
            "x": 0,
            "y": 0,
            "label": record.label,
        }
        for record in records
    ]

    directed_edges: list[dict[str, object]] = []
    for left, right in sorted(undirected_edges):
        distance_km = distances[(left, right)]
        approx_time_minutes = max((distance_km / 60.0) * 60.0, 0.1)
        directed_edges.append(
            {
                "from": str(left),
                "to": str(right),
                "weight": round(approx_time_minutes, 2),
                "distance_km": round(distance_km, 3),
            }
        )
        directed_edges.append(
            {
                "from": str(right),
                "to": str(left),
                "weight": round(approx_time_minutes, 2),
                "distance_km": round(distance_km, 3),
            }
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    NODES_OUTPUT.write_text(json.dumps(nodes, indent=2), encoding="utf-8")
    EDGES_OUTPUT.write_text(json.dumps(directed_edges, indent=2), encoding="utf-8")

    return nodes, directed_edges


def main() -> None:
    nodes, edges = export_scats_graph()
    print(f"Saved {len(nodes)} SCATS nodes to {NODES_OUTPUT}")
    print(f"Saved {len(edges)} directed SCATS edges to {EDGES_OUTPUT}")


if __name__ == "__main__":
    main()
