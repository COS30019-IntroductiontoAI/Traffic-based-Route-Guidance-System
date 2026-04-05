from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Hardcode path for Render deployment, with fallback for local development
# Render deploys to: /opt/render/project/src/
# Our config.py is at: /opt/render/project/src/backend/core/config.py
# So PROJECT_ROOT = /opt/render/project/src

if "RENDER" in os.environ:
    # Running on Render - use hardcoded path
    PROJECT_ROOT = Path("/opt/render/project/src")
else:
    # Local development - use dynamic resolution
    # The config.py file is at: PROJECT_ROOT/backend/core/config.py
    # So we go up 2 levels to reach PROJECT_ROOT
    PROJECT_ROOT = Path(__file__).resolve().parents[2]

print(f"Using PROJECT_ROOT: {PROJECT_ROOT}", file=sys.stderr)
print(f"RENDER env var: {os.environ.get('RENDER', 'Not set')}", file=sys.stderr)

__all__ = [
    "PROJECT_ROOT",
    "CONFIG_DIR",
    "BACKEND_CONFIG_PATH",
    "GENERATED_DIR",
    "PREDICTIONS_DIR",
    "SUPPORTED_DATA_KEYS",
    "ROUTE_GUIDANCE_MONTH",
    "ROUTE_GUIDANCE_MONTH_LABEL",
    "MAX_ROUTE_K",
    "TRAFFIC_PROFILE_HOUR_STEP",
    "GRAPH_NEIGHBORS_PER_SITE",
    "GRAPH_COMPONENT_QUERY_NEIGHBORS",
    "SCATS_COORDINATE_CORRECTIONS",
    "DEFAULT_ROUTE_GUIDANCE_SELECTION",
    "normalize_data_key",
    "get_scats_nodes_path",
    "get_scats_edges_path",
    "get_predictions_path",
    "get_route_guidance_defaults_payload",
    "get_default_data_key",
    "get_default_date",
    "get_default_time_of_day",
]

CONFIG_DIR = PROJECT_ROOT / "config"
BACKEND_CONFIG_PATH = CONFIG_DIR / "backend_config.json"

GENERATED_DIR = PROJECT_ROOT / "backend" / "generated"
SCATS_NODES_PATH = GENERATED_DIR / "scats_nodes.json"
SCATS_EDGES_PATH = GENERATED_DIR / "scats_edges.json"

PREDICTIONS_DIR = PROJECT_ROOT / "src" / "results" / "predictions"
PREDICTIONS_2006_PATH = PREDICTIONS_DIR / "2006_predictions.csv"
PREDICTIONS_2014_PATH = PREDICTIONS_DIR / "2014_predictions.csv"

# Ensure the backend configuration file is loaded dynamically with better error handling.
def _load_backend_config() -> dict:
    """Load backend configuration with clear error messages."""
    if not BACKEND_CONFIG_PATH.exists():
        error_msg = (
            f"Backend configuration file not found at {BACKEND_CONFIG_PATH}\n"
            f"PROJECT_ROOT resolved to: {PROJECT_ROOT}\n"
            f"CONFIG_DIR: {CONFIG_DIR}\n"
            f"This file should exist in the config/ directory at the project root."
        )
        print(error_msg, file=sys.stderr)
        raise FileNotFoundError(error_msg)
    
    try:
        with BACKEND_CONFIG_PATH.open("r", encoding="utf-8") as config_file:
            return json.load(config_file)
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse backend configuration JSON at {BACKEND_CONFIG_PATH}: {e}"
        print(error_msg, file=sys.stderr)
        raise ValueError(error_msg) from e

_RAW_BACKEND_CONFIG = _load_backend_config()

SUPPORTED_DATA_KEYS = set(_RAW_BACKEND_CONFIG["supported_data_keys"])
ROUTE_GUIDANCE_MONTH = int(_RAW_BACKEND_CONFIG["route_guidance_month"])
ROUTE_GUIDANCE_MONTH_LABEL = str(_RAW_BACKEND_CONFIG["route_guidance_month_label"])
MAX_ROUTE_K = int(_RAW_BACKEND_CONFIG["max_route_k"])
TRAFFIC_PROFILE_HOUR_STEP = int(_RAW_BACKEND_CONFIG["traffic_profile_hour_step"])
GRAPH_NEIGHBORS_PER_SITE = int(_RAW_BACKEND_CONFIG["graph_neighbors_per_site"])
GRAPH_COMPONENT_QUERY_NEIGHBORS = int(_RAW_BACKEND_CONFIG["graph_component_query_neighbors"])

SCATS_COORDINATE_CORRECTIONS: dict[int, tuple[float, float]] = {
    int(scats_number): (float(coords[0]), float(coords[1]))
    for scats_number, coords in _RAW_BACKEND_CONFIG["scats_coordinate_corrections"].items()
}

DEFAULT_ROUTE_GUIDANCE_SELECTION = _RAW_BACKEND_CONFIG["default_route_guidance_selection"]

# Normalize dataset keys to ensure compatibility.
def normalize_data_key(data_key: str = "2014") -> str:
    normalized = data_key.strip().lower()
    if normalized not in SUPPORTED_DATA_KEYS:
        raise ValueError(f"Unsupported dataset '{data_key}'")
    return normalized

# Dynamically resolve paths for generated files.
def get_scats_nodes_path(data_key: str = "2014") -> Path:
    normalized = normalize_data_key(data_key)
    return GENERATED_DIR / f"scats_nodes_{normalized}.json"

def get_scats_edges_path(data_key: str = "2014") -> Path:
    normalized = normalize_data_key(data_key)
    return GENERATED_DIR / f"scats_edges_{normalized}.json"

def get_predictions_path(data_key: str = "2014") -> Path:
    """
    Dynamically resolve the predictions file path for the given dataset key.
    """
    normalized = normalize_data_key(data_key)
    return PREDICTIONS_DIR / f"{normalized}_predictions.csv"

def get_route_guidance_defaults_payload() -> dict:
    """
    Return the default route guidance payload from the backend configuration.
    This is used to initialize the frontend with default values.
    """
    supported_data = sorted(SUPPORTED_DATA_KEYS)
    return {
        "supported_data": supported_data,
        "month": ROUTE_GUIDANCE_MONTH,
        "month_label": ROUTE_GUIDANCE_MONTH_LABEL,
        "defaults": {
            "data": get_default_data_key(),
            "time": get_default_time_of_day(),
            "date_by_data": {
                data_key: get_default_date(data_key)
                for data_key in supported_data
            },
        },
    }

def get_default_data_key() -> str:
    """
    Return the default dataset key shown when Route Guidance first loads.
    """
    default_data_key = str(DEFAULT_ROUTE_GUIDANCE_SELECTION.get("data", "2014"))
    try:
        return normalize_data_key(default_data_key)
    except ValueError:
        return "2014"

def get_default_date(data_key: str = "2014") -> str:
    """
    Return the default date for route guidance from configuration.
    Supports both legacy "date" and year-specific "date_by_data" config.
    """
    normalized_data_key = normalize_data_key(data_key)
    date_by_data = DEFAULT_ROUTE_GUIDANCE_SELECTION.get("date_by_data")

    if isinstance(date_by_data, dict):
        configured_date = date_by_data.get(normalized_data_key)
        if isinstance(configured_date, str) and configured_date:
            return configured_date

    legacy_date = DEFAULT_ROUTE_GUIDANCE_SELECTION.get("date")
    if isinstance(legacy_date, str) and legacy_date:
        return legacy_date

    return f"{normalized_data_key}-{ROUTE_GUIDANCE_MONTH:02d}-01"

def get_default_time_of_day() -> str:
    """
    Return the default time of day for route guidance from configuration.
    """
    return DEFAULT_ROUTE_GUIDANCE_SELECTION.get("time", "08:00")
