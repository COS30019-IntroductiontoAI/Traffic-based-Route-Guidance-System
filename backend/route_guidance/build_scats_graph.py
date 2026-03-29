from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from backend.core.config import GENERATED_DIR, SUPPORTED_DATA_KEYS, normalize_data_key
from backend.route_guidance.travel_time import free_flow_time_minutes
from backend.route_guidance.heuristic import haversine_distance_km


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "src" / "data" / "processed"
SITE_LISTING_PATH = PROCESSED_DIR / "SCATSSiteListingSpreadsheet_VicRoads_clean.csv"

# Manual coordinate corrections for SCATS sites whose recorded GPS coordinates are
# clearly wrong. The raw rows for 4266 include zero/out-of-region coordinates.
COORDINATE_CORRECTIONS: dict[int, tuple[float, float]] = {
    4266: (-37.8246, 145.0396),
}


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
        return fallback

    raise FileNotFoundError(f"Could not find a processed traffic CSV for dataset '{data_key}'")


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
    traffic_df = pd.read_csv(traffic_path)
    listing_df = pd.read_csv(SITE_LISTING_PATH).rename(columns={"site_number": "scats_number"})

    longitude_column = _get_longitude_column(traffic_df)

    coordinate_df = traffic_df[["scats_number", "nb_latitude", longitude_column]].copy()
    coordinate_df = coordinate_df.rename(columns={longitude_column: "nb_longitude"})
    coordinate_df["nb_latitude"] = pd.to_numeric(coordinate_df["nb_latitude"], errors="coerce")
    coordinate_df["nb_longitude"] = pd.to_numeric(coordinate_df["nb_longitude"], errors="coerce")

    # Ignore obviously broken coordinates before aggregating site locations.
    coordinate_df = coordinate_df[
        coordinate_df["nb_latitude"].between(-39.5, -33.5)
        & coordinate_df["nb_longitude"].between(140.0, 150.5)
    ]

    coordinate_summary = (
        coordinate_df.groupby("scats_number", observed=False)
        .agg(
            nb_latitude=("nb_latitude", "median"),
            nb_longitude=("nb_longitude", "median"),
        )
        .reset_index()
    )

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

        if scats_number in COORDINATE_CORRECTIONS:
            lat, lng = COORDINATE_CORRECTIONS[scats_number]

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


# Precompute pairwise distances between every site in the graph.
def build_distance_table(records: list[SiteRecord]) -> dict[tuple[int, int], float]:
    distances: dict[tuple[int, int], float] = {}
    for index, left in enumerate(records):
        for right in records[index + 1 :]:
            distance_km = haversine_distance_km(left.lat, left.lng, right.lat, right.lng)
            distances[(left.scats_number, right.scats_number)] = distance_km
            distances[(right.scats_number, left.scats_number)] = distance_km
    return distances


# Connect each site to a small number of nearby neighbors.
def connect_nearest_neighbors(
    records: list[SiteRecord],
    distances: dict[tuple[int, int], float],
    neighbors_per_site: int = 3,
) -> set[tuple[int, int]]:
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
            undirected_edges.add(tuple(sorted((site.scats_number, neighbor))))

    return undirected_edges


# Add extra links between sites that appear to share the same road corridor.
def connect_same_road_sites(
    records: list[SiteRecord],
    distances: dict[tuple[int, int], float],
) -> set[tuple[int, int]]:
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
                undirected_edges.add(tuple(sorted((site.scats_number, same_road_neighbors[0][1]))))

    return undirected_edges


# Return the connected components of the current undirected graph.
def connected_components(records: list[SiteRecord], edges: set[tuple[int, int]]) -> list[set[int]]:
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
    distances: dict[tuple[int, int], float],
    edges: set[tuple[int, int]],
) -> set[tuple[int, int]]:
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

    return edges


# Generate and save the frontend-ready graph JSON for one dataset year.
def export_scats_graph(data_key: str) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    normalized = normalize_data_key(data_key)
    records = load_site_records(normalized)
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
