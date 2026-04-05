from __future__ import annotations

import json
from pathlib import Path

# Dynamically resolve the project root to ensure compatibility with deployment environments.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
BACKEND_CONFIG_PATH = CONFIG_DIR / "backend_config.json"

GENERATED_DIR = PROJECT_ROOT / "backend" / "generated"
SCATS_NODES_PATH = GENERATED_DIR / "scats_nodes.json"
SCATS_EDGES_PATH = GENERATED_DIR / "scats_edges.json"

PREDICTIONS_DIR = PROJECT_ROOT / "src" / "results" / "predictions"
PREDICTIONS_2006_PATH = PREDICTIONS_DIR / "2006_predictions.csv"
PREDICTIONS_2014_PATH = PREDICTIONS_DIR / "2014_predictions.csv"

# Ensure the backend configuration file is loaded dynamically.
with BACKEND_CONFIG_PATH.open("r", encoding="utf-8") as config_file:
    _RAW_BACKEND_CONFIG = json.load(config_file)

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
