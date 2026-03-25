from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

FRONTEND_NODES_PATH = PROJECT_ROOT / "frontend" / "src" / "components" / "route-guidance" / "nodes.json"
FRONTEND_EDGES_PATH = PROJECT_ROOT / "frontend" / "src" / "components" / "route-guidance" / "edges.json"
SCATS_NODES_PATH = PROJECT_ROOT / "backend" / "generated" / "scats_nodes.json"
SCATS_EDGES_PATH = PROJECT_ROOT / "backend" / "generated" / "scats_edges.json"

LIGHTGBM_MODEL_PATH = PROJECT_ROOT / "results" / "trained_models" / "lightgbm_model.txt"
LIGHTGBM_METADATA_PATH = PROJECT_ROOT / "results" / "trained_models" / "lightgbm_metadata.json"
PREDICTIONS_DIR = PROJECT_ROOT / "results" / "predictions"
PREDICTIONS_2006_PATH = PREDICTIONS_DIR / "2006_predictions.csv"
PREDICTIONS_2014_PATH = PROJECT_ROOT / "results" / "predictions" / "2014_predictions.csv"


# Resolve a prepared predictions CSV path from a supported dataset key.
def get_predictions_path(data_key: str = "2014") -> Path:
    normalized = data_key.strip().lower()
    if normalized == "2006":
        return PREDICTIONS_2006_PATH
    if normalized == "2014":
        return PREDICTIONS_2014_PATH
    raise ValueError(f"Unsupported predictions dataset '{data_key}'")
