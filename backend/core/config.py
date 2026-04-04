from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
BACKEND_CONFIG_PATH = CONFIG_DIR / "backend_config.json"

GENERATED_DIR = PROJECT_ROOT / "backend" / "generated"
SCATS_NODES_PATH = GENERATED_DIR / "scats_nodes.json"
SCATS_EDGES_PATH = GENERATED_DIR / "scats_edges.json"

PREDICTIONS_DIR = PROJECT_ROOT / "src" / "results" / "predictions"
PREDICTIONS_2006_PATH = PREDICTIONS_DIR / "2006_predictions.csv"
PREDICTIONS_2014_PATH = PREDICTIONS_DIR / "2014_predictions.csv"

# Keep backend settings in JSON so this file stays as a readable Python adapter.
# Other backend modules still import normal constants from here, but the values
# now come from one editable config source instead of being redefined inline.
with BACKEND_CONFIG_PATH.open("r", encoding="utf-8") as config_file:
    _RAW_BACKEND_CONFIG = json.load(config_file)

# The backend only supports the prepared dataset years shipped with the project.
# Keeping the values explicit still lets request validation fail early.
SUPPORTED_DATA_KEYS = set(_RAW_BACKEND_CONFIG["supported_data_keys"])

# Route Guidance is intentionally scoped to October because the prepared routing
# data and UI defaults are built around that month in both datasets.
ROUTE_GUIDANCE_MONTH = int(_RAW_BACKEND_CONFIG["route_guidance_month"])
ROUTE_GUIDANCE_MONTH_LABEL = str(_RAW_BACKEND_CONFIG["route_guidance_month_label"])

# Cap top-k at the API layer so route search stays bounded and predictable.
MAX_ROUTE_K = int(_RAW_BACKEND_CONFIG["max_route_k"])

# Keep dashboard traffic charts readable by sampling every few hours instead of every interval.
TRAFFIC_PROFILE_HOUR_STEP = int(_RAW_BACKEND_CONFIG["traffic_profile_hour_step"])

# Keep graph degree small because this graph is only a routing scaffold, not a full road network.
GRAPH_NEIGHBORS_PER_SITE = int(_RAW_BACKEND_CONFIG["graph_neighbors_per_site"])

# Expand cross-component neighbor search gradually instead of scanning every site globally.
GRAPH_COMPONENT_QUERY_NEIGHBORS = int(_RAW_BACKEND_CONFIG["graph_component_query_neighbors"])

# Store known coordinate corrections in JSON so they remain visible to the team
# and do not disappear inside graph-building logic.
SCATS_COORDINATE_CORRECTIONS: dict[int, tuple[float, float]] = {
    int(scats_number): (float(coords[0]), float(coords[1]))
    for scats_number, coords in _RAW_BACKEND_CONFIG["scats_coordinate_corrections"].items()
}

# These defaults drive the first state shown in the route-guidance UI.
# They are grouped in JSON so frontend-facing defaults and backend validation
# can stay aligned without duplicating the same values in multiple files.
DEFAULT_ROUTE_GUIDANCE_SELECTION = _RAW_BACKEND_CONFIG["default_route_guidance_selection"]


# Normalize a dataset key and reject unsupported values early.
def normalize_data_key(data_key: str = "2014") -> str:
    normalized = data_key.strip().lower()
    if normalized not in SUPPORTED_DATA_KEYS:
        raise ValueError(f"Unsupported dataset '{data_key}'")
    return normalized


# Return the year-specific generated nodes file path.
def get_scats_nodes_path(data_key: str = "2014") -> Path:
    normalized = normalize_data_key(data_key)
    return GENERATED_DIR / f"scats_nodes_{normalized}.json"


# Return the year-specific generated edges file path.
def get_scats_edges_path(data_key: str = "2014") -> Path:
    normalized = normalize_data_key(data_key)
    return GENERATED_DIR / f"scats_edges_{normalized}.json"


# Return the default dataset shown when Route Guidance first loads.
def get_default_data_key() -> str:
    return normalize_data_key(str(DEFAULT_ROUTE_GUIDANCE_SELECTION["data"]))


# Return the default date for the selected dataset year.
def get_default_date(data_key: str) -> str:
    normalized = normalize_data_key(data_key)
    date_by_data = DEFAULT_ROUTE_GUIDANCE_SELECTION.get("date_by_data", {})
    configured = str(date_by_data.get(normalized, ""))
    if configured:
        return configured
    # Fall back to a reasonable October date if config is incomplete.
    return f"{normalized}-10-17"


# Return the default time-of-day used by Route Guidance.
def get_default_time_of_day() -> str:
    return str(DEFAULT_ROUTE_GUIDANCE_SELECTION["time"])


# Build the frontend config payload for the Option 1 date-and-time UI.
def get_route_guidance_defaults_payload() -> dict[str, object]:
    # The frontend should learn valid defaults from one place instead of duplicating them in UI code.
    return {
        "supported_data": sorted(SUPPORTED_DATA_KEYS),
        "month": ROUTE_GUIDANCE_MONTH,
        "month_label": ROUTE_GUIDANCE_MONTH_LABEL,
        "defaults": {
            "data": get_default_data_key(),
            "time": get_default_time_of_day(),
            "date_by_data": {
                data_key: get_default_date(data_key)
                for data_key in sorted(SUPPORTED_DATA_KEYS)
            },
        },
    }


# Resolve a prepared predictions CSV path from a supported dataset key.
def get_predictions_path(data_key: str = "2014") -> Path:
    normalized = normalize_data_key(data_key)
    # Prediction CSVs are prepared offline by the shared src pipeline.
    # The backend only looks them up by dataset year.
    if normalized == "2006":
        return PREDICTIONS_2006_PATH
    return PREDICTIONS_2014_PATH
