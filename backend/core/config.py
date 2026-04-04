from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

GENERATED_DIR = PROJECT_ROOT / "backend" / "generated"
SCATS_NODES_PATH = GENERATED_DIR / "scats_nodes.json"
SCATS_EDGES_PATH = GENERATED_DIR / "scats_edges.json"

PREDICTIONS_DIR = PROJECT_ROOT / "src" / "results" / "predictions"
PREDICTIONS_2006_PATH = PREDICTIONS_DIR / "2006_predictions.csv"
PREDICTIONS_2014_PATH = PREDICTIONS_DIR / "2014_predictions.csv"

# The backend only supports the two prepared datasets shipped with the project.
# Keeping the allowed keys explicit makes routing requests fail early when the UI sends a bad year.
SUPPORTED_DATA_KEYS = {"2006", "2014"}

# Route Guidance is intentionally scoped to October because the prepared routing data and UI defaults
# are built around that month in both datasets.
ROUTE_GUIDANCE_MONTH = 10
ROUTE_GUIDANCE_MONTH_LABEL = "October"

# Cap top-k at the API layer so route search stays bounded and predictable.
MAX_ROUTE_K = 5

# Keep dashboard traffic charts readable by sampling every few hours instead of every interval.
TRAFFIC_PROFILE_HOUR_STEP = 3

# Keep graph degree small because this graph is only a routing scaffold, not a full road network.
GRAPH_NEIGHBORS_PER_SITE = 3

# Expand cross-component neighbor search gradually instead of scanning every site globally.
GRAPH_COMPONENT_QUERY_NEIGHBORS = 8

# Store known coordinate corrections in config so they are visible and not hidden inside graph code.
SCATS_COORDINATE_CORRECTIONS: dict[int, tuple[float, float]] = {
    4266: (-37.8246, 145.0396),
}

# These defaults drive the first state shown in the route-guidance UI.
# They are grouped here so frontend and backend can stay consistent.
DEFAULT_ROUTE_GUIDANCE_SELECTION = {
    "data": "2014",
    "date_by_data": {
        "2006": "2006-10-17",
        "2014": "2014-10-17",
    },
    "time": "08:00",
}


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
