"""Model configuration loader backed by external JSON configuration."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
CONFIG_PATH: Path = PROJECT_ROOT / "config" / "model_config.json"


def _load_config(config_path: Path) -> dict[str, Any]:
  """Load raw model configuration data from disk."""
  if not config_path.exists():
    raise FileNotFoundError(f"Model configuration file not found: {config_path}")

  with config_path.open("r", encoding="utf-8") as config_file:
    config_data = json.load(config_file)

  if not isinstance(config_data, dict):
    raise ValueError("Model configuration JSON root must be an object.")

  LOGGER.info("Loaded model configuration from %s", config_path)
  return config_data


def _require(config_data: dict[str, Any], key: str) -> Any:
  """Return one required configuration value."""
  if key not in config_data:
    raise KeyError(f"Missing required configuration key: {key}")
  return config_data[key]


CONFIG_DATA: dict[str, Any] = _load_config(CONFIG_PATH)

SEQ_LEN: int = int(_require(CONFIG_DATA, "SEQ_LEN"))
FORECAST_HORIZON: int = int(_require(CONFIG_DATA, "FORECAST_HORIZON"))
INPUT_FEATURES: int = int(_require(CONFIG_DATA, "INPUT_FEATURES"))

EPOCHS: int = int(_require(CONFIG_DATA, "EPOCHS"))
BATCH_SIZE: int = int(_require(CONFIG_DATA, "BATCH_SIZE"))
LEARNING_RATE: float = float(_require(CONFIG_DATA, "LEARNING_RATE"))
DROPOUT_RATE: float = float(_require(CONFIG_DATA, "DROPOUT_RATE"))
L2_REG: float = float(_require(CONFIG_DATA, "L2_REG"))

EARLY_STOP_PATIENCE: int = int(_require(CONFIG_DATA, "EARLY_STOP_PATIENCE"))
LR_REDUCE_PATIENCE: int = int(_require(CONFIG_DATA, "LR_REDUCE_PATIENCE"))
LR_REDUCE_FACTOR: float = float(_require(CONFIG_DATA, "LR_REDUCE_FACTOR"))
MIN_LR: float = float(_require(CONFIG_DATA, "MIN_LR"))
MONITOR_METRIC: str = str(_require(CONFIG_DATA, "MONITOR_METRIC"))

LIGHTGBM_OBJECTIVE: str = str(_require(CONFIG_DATA, "LIGHTGBM_OBJECTIVE"))
LIGHTGBM_DEVICE: str = str(_require(CONFIG_DATA, "LIGHTGBM_DEVICE"))
LIGHTGBM_N_ESTIMATORS: int = int(_require(CONFIG_DATA, "LIGHTGBM_N_ESTIMATORS"))
LIGHTGBM_LEARNING_RATE: float = float(_require(CONFIG_DATA, "LIGHTGBM_LEARNING_RATE"))
LIGHTGBM_NUM_LEAVES: int = int(_require(CONFIG_DATA, "LIGHTGBM_NUM_LEAVES"))
LIGHTGBM_MAX_DEPTH: int = int(_require(CONFIG_DATA, "LIGHTGBM_MAX_DEPTH"))
LIGHTGBM_MIN_CHILD_SAMPLES: int = int(_require(CONFIG_DATA, "LIGHTGBM_MIN_CHILD_SAMPLES"))
LIGHTGBM_SUBSAMPLE: float = float(_require(CONFIG_DATA, "LIGHTGBM_SUBSAMPLE"))
LIGHTGBM_COLSAMPLE_BYTREE: float = float(_require(CONFIG_DATA, "LIGHTGBM_COLSAMPLE_BYTREE"))
LIGHTGBM_REG_ALPHA: float = float(_require(CONFIG_DATA, "LIGHTGBM_REG_ALPHA"))
LIGHTGBM_REG_LAMBDA: float = float(_require(CONFIG_DATA, "LIGHTGBM_REG_LAMBDA"))
LIGHTGBM_RANDOM_STATE: int = int(_require(CONFIG_DATA, "LIGHTGBM_RANDOM_STATE"))
LIGHTGBM_VERBOSE: int = int(_require(CONFIG_DATA, "LIGHTGBM_VERBOSE"))
LIGHTGBM_EVAL_METRIC: str = str(_require(CONFIG_DATA, "LIGHTGBM_EVAL_METRIC"))
LIGHTGBM_EARLY_STOPPING_ROUNDS: int = int(_require(CONFIG_DATA, "LIGHTGBM_EARLY_STOPPING_ROUNDS"))

# Keep these metadata fields here so the LightGBM artifact schema is still defined
# next to the rest of the model configuration.
LIGHTGBM_TARGET_COLUMN: str = "traffic_volume"
LIGHTGBM_CATEGORICAL_FEATURES: list[str] = ["scats_number", "location"]
