from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

GENERATED_DIR = PROJECT_ROOT / "backend" / "generated"
SCATS_NODES_PATH = GENERATED_DIR / "scats_nodes.json"
SCATS_EDGES_PATH = GENERATED_DIR / "scats_edges.json"

PREDICTIONS_DIR = PROJECT_ROOT / "src" / "results" / "predictions"
PREDICTIONS_2006_PATH = PREDICTIONS_DIR / "2006_predictions.csv"
PREDICTIONS_2014_PATH = PREDICTIONS_DIR / "2014_predictions.csv"

SUPPORTED_DATA_KEYS = {"2006", "2014"}
ROUTE_GUIDANCE_MONTH = 10
ROUTE_GUIDANCE_MONTH_LABEL = "October"

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
    return f"{normalized}-10-17"


# Return the default time-of-day used by Route Guidance.
def get_default_time_of_day() -> str:
    return str(DEFAULT_ROUTE_GUIDANCE_SELECTION["time"])


# Build the frontend config payload for the Option 1 date-and-time UI.
def get_route_guidance_defaults_payload() -> dict[str, object]:
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
# Return the prepared predictions CSV path for the selected dataset.
def get_predictions_path(data_key: str = "2014") -> Path:
    normalized = normalize_data_key(data_key)
    if normalized == "2006":
        return PREDICTIONS_2006_PATH
    return PREDICTIONS_2014_PATH
