from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree

from backend.core.config import (
    GENERATED_DIR,
    GRAPH_COMPONENT_QUERY_NEIGHBORS,
    GRAPH_NEIGHBORS_PER_SITE,
    SCATS_COORDINATE_CORRECTIONS,
    SUPPORTED_DATA_KEYS,
    normalize_data_key,
)
from backend.route_guidance.travel_time import free_flow_time_minutes
from backend.route_guidance.heuristic import haversine_distance_km


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "src" / "data" / "processed"
SITE_LISTING_PATH = PROCESSED_DIR / "SCATSSiteListingSpreadsheet_VicRoads_clean.csv"

# Store the site metadata needed to build the route graph.
@dataclass(slots=True)
class SiteRecord:
    scats_number: int
    lat: float
    lng: float
    road_name: str
    label: str


# Resolve the processed traffic file for the selected dataset year.
def _get_processed_traffic_path(data_key: str) -> Path:
    normalized = normalize_data_key(data_key)
    preferred = PROCESSED_DIR / f"{normalized}_processed.csv"
    if preferred.exists():
        return preferred

    fallback = PROCESSED_DIR / "cleaned_traffic.csv"
    if fallback.exists():
        # Keep the fallback only for older local setups that have not been split by year yet.
        return fallback

    raise FileNotFoundError(
        f"Could not find a processed traffic CSV for dataset '{data_key}'. "
        f"Looked in: {PROCESSED_DIR}. "
        f"Please ensure the processed data files exist or run the preprocessing pipeline first."
    )


# Detect the longitude column name used by the processed dataset.
def _get_longitude_column(dataframe: pd.DataFrame) -> str:
    for candidate in ("nb_longitude", "nb_longtitude"):
        if candidate in dataframe.columns:
            return candidate
    raise KeyError("Processed traffic CSV is missing both 'nb_longitude' and 'nb_longtitude'")


# Return the most representative text value from a grouped series.
def _series_mode_or_first(series: pd.Series) -> object:
    mode = series.mode(dropna=True)
    if not mode.empty:
        return mode.iloc[0]
    return series.dropna().iloc[0] if not series.dropna().empty else ""


# Build one cleaned site record per SCATS intersection for a dataset year.
def load_site_records(data_key: str) -> list[SiteRecord]:
    traffic_path = _get_processed_traffic_path(data_key)
    
    # Validate that the site listing file exists
    if not SITE_LISTING_PATH.exists():
        raise FileNotFoundError(
            f"SCATS site listing file not found at {SITE_LISTING_PATH}. "
            f"This file is required to build the route graph."
        )
    
    traffic_df = pd.read_csv(traffic_path)
    listing_df = pd.read_csv(SITE_LISTING_PATH).rename(columns={"site_number": "scats_number"})

    longitude_column = _get_longitude_column(traffic_df)

    coordinate_df = traffic_df[["scats_number", "nb_latitude", longitude_column]].copy()
    coordinate_df = coordinate_df.rename(columns={longitude_column: "nb_longitude"})
    coordinate_df["nb_latitude"] = pd.to_numeric(coordinate_df["nb_latitude"], errors="coerce")
    coordinate_df["nb_longitude"] = pd.to_numeric(coordinate_df["nb_longitude"], errors="coerce")

    # The processed files may still contain occasional bad coordinates.
    # Filter them out before building one site record per SCATS node.
    coordinate_df = coordinate_df[
        coordinate_df["nb_latitude"].between(-39.5, -33.5)
        & coordinate_df["nb_longitude"].between(140.0, 150.5)
    ]

    # We use the median coordinate per site so one noisy row does not drag the node to a bad location.
    coordinate_summary = (
        coordinate_df.groupby("scats_number", observed=False)
        .agg(
            nb_latitude=("nb_latitude", "median"),
            nb_longitude=("nb_longitude", "median"),
        )
        .reset_index()
    )

    # The road name acts as a weak corridor clue later when we add same-road links.
    metadata_summary = (
        traffic_df.groupby("scats_number", observed=False)
        .agg(
            road_name=("road_name", _series_mode_or_first),
        )
        .reset_index()
    )

    site_df = coordinate_summary.merge(metadata_summary, on="scats_number", how="left")
    site_df = site_df.merge(
        listing_df[["scats_number", "location_description"]],
        on="scats_number",
        how="left",
    )

    records: list[SiteRecord] = []
    for row in site_df.itertuples(index=False):
        scats_number = int(row.scats_number)
        label = row.location_description if pd.notna(row.location_description) else row.road_name
        lat = float(row.nb_latitude)
        lng = float(row.nb_longitude)

        # Keep manual corrections explicit because these are known bad raw coordinates, not learned changes.
        if scats_number in SCATS_COORDINATE_CORRECTIONS:
            lat, lng = SCATS_COORDINATE_CORRECTIONS[scats_number]

        if not (-39.5 < lat < -33.5 and 140.0 < lng < 150.5):
            continue

        records.append(
            SiteRecord(
                scats_number=scats_number,
                lat=lat,
                lng=lng,
                road_name=str(row.road_name),
                label=str(label),
            )
        )

    return records


# Compute one site-to-site distance lazily and cache it for later reuse.
def _distance_between(
    left: SiteRecord,
    right: SiteRecord,
    distance_cache: dict[tuple[int, int], float],
) -> float:
    if left.scats_number == right.scats_number:
        return 0.0

    cache_key = tuple(sorted((left.scats_number, right.scats_number)))
    if cache_key not in distance_cache:
        distance_cache[cache_key] = haversine_distance_km(left.lat, left.lng, right.lat, right.lng)
    return distance_cache[cache_key]


# Build a spatial index once so nearest-neighbor queries do not require repeated full scans.
def _build_spatial_index(records: list[SiteRecord]) -> tuple[BallTree, np.ndarray, list[SiteRecord]]:
    # BallTree with haversine distance gives us fast geographic nearest-neighbor search on lat/lng data.
    coordinates_radians = np.radians(np.array([[record.lat, record.lng] for record in records], dtype=float))
    return BallTree(coordinates_radians, metric="haversine"), coordinates_radians, records


# Convert BallTree haversine output into kilometers.
def _haversine_radians_to_km(distance_radians: float) -> float:
    return float(distance_radians) * 6371.0088


# Find the nearest site that belongs to a different connected component.
def _find_cross_component_neighbor(
    site_index: int,
    component_by_site: dict[int, int],
    tree: BallTree,
    coordinates_radians: np.ndarray,
    records: list[SiteRecord],
) -> tuple[float, int] | None:
    current_site = records[site_index]
    current_component = component_by_site[current_site.scats_number]
    candidate_count = min(len(records), GRAPH_COMPONENT_QUERY_NEIGHBORS)

    while candidate_count <= len(records):
        # Query progressively more neighbors until we find a site outside the current component.
        # This avoids comparing against every node up front.
        distances_radians, indices = tree.query(coordinates_radians[[site_index]], k=candidate_count)
        for distance_radians, neighbor_index in zip(distances_radians[0], indices[0]):
            neighbor = records[int(neighbor_index)]
            if neighbor.scats_number == current_site.scats_number:
                continue
            if component_by_site[neighbor.scats_number] == current_component:
                continue
            return _haversine_radians_to_km(float(distance_radians)), int(neighbor_index)

        if candidate_count == len(records):
            break
        candidate_count = min(len(records), candidate_count * 2)

    return None


# Connect each site to a small number of nearby neighbors.
def connect_nearest_neighbors(
    records: list[SiteRecord],
    distance_cache: dict[tuple[int, int], float],
    neighbors_per_site: int = GRAPH_NEIGHBORS_PER_SITE,
) -> set[tuple[int, int]]:
    undirected_edges: set[tuple[int, int]] = set()
    tree, _, ordered_records = _build_spatial_index(records)

    # Query only a handful of nearest neighbors because we only need a sparse graph, not all pairwise links.
    coordinates_radians = np.radians(np.array([[record.lat, record.lng] for record in records], dtype=float))
    distances_radians, indices = tree.query(coordinates_radians, k=min(len(records), neighbors_per_site + 1))

    for site_index, site in enumerate(ordered_records):
        for neighbor_index in indices[site_index]:
            neighbor = ordered_records[int(neighbor_index)]
            if neighbor.scats_number == site.scats_number:
                continue

            # Distances are still cached explicitly because later graph-building stages may ask for the
            # same pair again when they add same-road links or component bridges.
            _distance_between(site, neighbor, distance_cache)
            undirected_edges.add(tuple(sorted((site.scats_number, neighbor.scats_number))))

    return undirected_edges


# Add extra links between sites that appear to share the same road corridor.
def connect_same_road_sites(
    records: list[SiteRecord],
    distance_cache: dict[tuple[int, int], float],
) -> set[tuple[int, int]]:
    undirected_edges: set[tuple[int, int]] = set()
    by_road: dict[str, list[SiteRecord]] = {}

    for site in records:
        by_road.setdefault(site.road_name, []).append(site)

    # Same-road links act as a second heuristic so the graph is not purely distance-based.
    for road_sites in by_road.values():
        if len(road_sites) < 2:
            continue

        for site in road_sites:
            same_road_neighbor = min(
                (
                    (_distance_between(site, other, distance_cache), other.scats_number)
                    for other in road_sites
                    if other.scats_number != site.scats_number
                ),
                default=None,
                key=lambda item: item[0],
            )
            if same_road_neighbor is not None:
                undirected_edges.add(tuple(sorted((site.scats_number, same_road_neighbor[1]))))

    return undirected_edges


# Return the connected components of the current undirected graph.
def connected_components(records: list[SiteRecord], edges: set[tuple[int, int]]) -> list[set[int]]:
    # Components are used only to ensure the final graph is fully routable.
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


# Join disconnected components until the graph becomes fully connected.
def connect_components(
    records: list[SiteRecord],
    distance_cache: dict[tuple[int, int], float],
    edges: set[tuple[int, int]],
) -> set[tuple[int, int]]:
    components = connected_components(records, edges)
    if len(components) <= 1:
        return edges

    # We search for nearest cross-component links through the spatial index so we do not
    # compare every site against every other site after each merge.
    component_index = {
        node_id: index
        for index, component in enumerate(components)
        for node_id in component
    }
    tree, coordinates_radians, ordered_records = _build_spatial_index(records)
    best_links: dict[tuple[int, int], tuple[float, tuple[int, int]]] = {}

    for site_index, site in enumerate(ordered_records):
        cross_component_neighbor = _find_cross_component_neighbor(
            site_index,
            component_index,
            tree,
            coordinates_radians,
            ordered_records,
        )
        if cross_component_neighbor is None:
            continue

        distance_km, neighbor_index = cross_component_neighbor
        neighbor = ordered_records[neighbor_index]
        _distance_between(site, neighbor, distance_cache)
        component_pair = tuple(sorted((component_index[site.scats_number], component_index[neighbor.scats_number])))
        edge_pair = tuple(sorted((site.scats_number, neighbor.scats_number)))

        current_best = best_links.get(component_pair)
        if current_best is None or distance_km < current_best[0]:
            best_links[component_pair] = (distance_km, edge_pair)

    # Union-find lets us add the cheapest component-bridging edges without repeatedly rebuilding components.
    component_parents = list(range(len(components)))

    def find(parent_index: int) -> int:
        while component_parents[parent_index] != parent_index:
            component_parents[parent_index] = component_parents[component_parents[parent_index]]
            parent_index = component_parents[parent_index]
        return parent_index

    def union(left_index: int, right_index: int) -> bool:
        left_root = find(left_index)
        right_root = find(right_index)
        if left_root == right_root:
            return False
        component_parents[right_root] = left_root
        return True

    for component_pair, (_, edge_pair) in sorted(best_links.items(), key=lambda item: item[1][0]):
        left_component, right_component = component_pair
        if union(left_component, right_component):
            # Only add the bridge when it actually merges two components.
            # This avoids cluttering the graph with redundant long-range edges.
            edges.add(edge_pair)

    return edges


# Generate and save the frontend-ready graph JSON for one dataset year.
def export_scats_graph(data_key: str) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    normalized = normalize_data_key(data_key)
    records = load_site_records(normalized)
    distance_cache: dict[tuple[int, int], float] = {}

    # The graph is built in layers:
    # 1) local nearest-neighbor links
    # 2) same-road links
    # 3) cross-component links for global connectivity
    undirected_edges = connect_nearest_neighbors(records, distance_cache, neighbors_per_site=GRAPH_NEIGHBORS_PER_SITE)
    undirected_edges |= connect_same_road_sites(records, distance_cache)
    undirected_edges = connect_components(records, distance_cache, undirected_edges)

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

    # The route engine expects directed edges, so each undirected connection is written both ways.
    directed_edges: list[dict[str, object]] = []
    records_by_id = {record.scats_number: record for record in records}
    for left, right in sorted(undirected_edges):
        distance_km = _distance_between(records_by_id[left], records_by_id[right], distance_cache)
        approx_time_minutes = max(free_flow_time_minutes(distance_km), 0.1)
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

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    nodes_output = GENERATED_DIR / f"scats_nodes_{normalized}.json"
    edges_output = GENERATED_DIR / f"scats_edges_{normalized}.json"
    nodes_output.write_text(json.dumps(nodes, indent=2), encoding="utf-8")
    edges_output.write_text(json.dumps(directed_edges, indent=2), encoding="utf-8")

    return nodes, directed_edges


# Parse CLI arguments for the graph export script.
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate SCATS route graphs from processed traffic data")
    parser.add_argument(
        "--data",
        default="all",
        choices=["all", *sorted(SUPPORTED_DATA_KEYS)],
        help="Dataset year to export",
    )
    return parser.parse_args()


# Export one or both year-specific SCATS graphs from the command line.
def main() -> None:
    args = _parse_args()
    target_datasets = sorted(SUPPORTED_DATA_KEYS) if args.data == "all" else [args.data]

    for data_key in target_datasets:
        nodes, edges = export_scats_graph(data_key)
        print(f"[{data_key}] Saved {len(nodes)} SCATS nodes")
        print(f"[{data_key}] Saved {len(edges)} directed SCATS edges")


if __name__ == "__main__":
    main()
