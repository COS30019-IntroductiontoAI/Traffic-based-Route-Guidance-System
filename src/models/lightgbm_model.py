from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from lightgbm import LGBMRegressor, early_stopping
import numpy as np
import pandas as pd

from src.config import model_config
from src.data_loader import prepare_tabular_data
from src.evaluation import evaluate_tabular_predictions, plot_predictions
from src.predict import predict_tabular_model

LOGGER = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRAINED_MODELS_DIR = PROJECT_ROOT / "results" / "trained_models"
METRICS_DIR = PROJECT_ROOT / "results" / "metrics"
GRAPHS_DIR = PROJECT_ROOT / "results" / "graphs"
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "2006_processed.csv"
MODEL_PATH = TRAINED_MODELS_DIR / "lightgbm_model.txt"
METADATA_PATH = TRAINED_MODELS_DIR / "lightgbm_metadata.json"
METRICS_PATH = METRICS_DIR / "lightgbm_metrics.json"

TARGET_COLUMN = "traffic_volume"

DEFAULT_SEQUENCE_LENGTH: int = int(getattr(model_config, "SEQ_LEN", 96))
DEFAULT_FORECAST_HORIZON: int = int(getattr(model_config, "FORECAST_HORIZON", 1))
DEFAULT_OBJECTIVE: str = str(getattr(model_config, "LIGHTGBM_OBJECTIVE", "poisson"))
DEFAULT_DEVICE: str = str(getattr(model_config, "LIGHTGBM_DEVICE", "cpu"))
DEFAULT_N_ESTIMATORS: int = int(getattr(model_config, "LIGHTGBM_N_ESTIMATORS", 2200))
DEFAULT_LEARNING_RATE: float = float(getattr(model_config, "LIGHTGBM_LEARNING_RATE", 0.03))
DEFAULT_NUM_LEAVES: int = int(getattr(model_config, "LIGHTGBM_NUM_LEAVES", 255))
DEFAULT_MAX_DEPTH: int = int(getattr(model_config, "LIGHTGBM_MAX_DEPTH", 12))
DEFAULT_MIN_CHILD_SAMPLES: int = int(getattr(model_config, "LIGHTGBM_MIN_CHILD_SAMPLES", 80))
DEFAULT_SUBSAMPLE: float = float(getattr(model_config, "LIGHTGBM_SUBSAMPLE", 1.0))
DEFAULT_COLSAMPLE_BYTREE: float = float(getattr(model_config, "LIGHTGBM_COLSAMPLE_BYTREE", 0.6))
DEFAULT_REG_ALPHA: float = float(getattr(model_config, "LIGHTGBM_REG_ALPHA", 0.05))
DEFAULT_REG_LAMBDA: float = float(getattr(model_config, "LIGHTGBM_REG_LAMBDA", 1.0))
DEFAULT_RANDOM_STATE: int = int(getattr(model_config, "LIGHTGBM_RANDOM_STATE", 42))
DEFAULT_VERBOSE: int = int(getattr(model_config, "LIGHTGBM_VERBOSE", -1))
DEFAULT_EVAL_METRIC: str = str(getattr(model_config, "LIGHTGBM_EVAL_METRIC", "rmse"))
DEFAULT_EARLY_STOPPING_ROUNDS: int = int(getattr(model_config, "LIGHTGBM_EARLY_STOPPING_ROUNDS", 80))


# Return feature matrix X and target vector y from a prepared dataframe.
def get_xy(df: pd.DataFrame, feature_columns: list[str]) -> tuple[pd.DataFrame, pd.Series]:
  """Return model matrix and target vector from a prepared split dataframe.

  Args:
    df: Prepared split dataframe.
    feature_columns: Ordered list of feature columns.

  Returns:
    Feature dataframe and target series tuple.
  """
  return df[feature_columns], df[TARGET_COLUMN]


# Build the shared LightGBM regressor for the tabular pipeline.
def create_model(
  objective: str = DEFAULT_OBJECTIVE,
  device: str = DEFAULT_DEVICE,
  n_estimators: int = DEFAULT_N_ESTIMATORS,
  learning_rate: float = DEFAULT_LEARNING_RATE,
  num_leaves: int = DEFAULT_NUM_LEAVES,
  max_depth: int = DEFAULT_MAX_DEPTH,
  min_child_samples: int = DEFAULT_MIN_CHILD_SAMPLES,
  subsample: float = DEFAULT_SUBSAMPLE,
  colsample_bytree: float = DEFAULT_COLSAMPLE_BYTREE,
  reg_alpha: float = DEFAULT_REG_ALPHA,
  reg_lambda: float = DEFAULT_REG_LAMBDA,
  random_state: int = DEFAULT_RANDOM_STATE,
  verbose: int = DEFAULT_VERBOSE,
) -> LGBMRegressor:
  """Build one LightGBM regressor from caller-provided or configured settings.

  Args:
    objective: LightGBM objective function.
    device: LightGBM compute device.
    n_estimators: Maximum number of boosting rounds.
    learning_rate: Gradient boosting learning rate.
    num_leaves: Maximum leaf count per tree.
    max_depth: Maximum tree depth.
    min_child_samples: Minimum child sample count.
    subsample: Row sampling ratio per tree.
    colsample_bytree: Column sampling ratio per tree.
    reg_alpha: L1 regularization strength.
    reg_lambda: L2 regularization strength.
    random_state: Random seed.
    verbose: LightGBM verbosity.

  Returns:
    Configured LightGBM regressor.
  """
  return LGBMRegressor(
    objective=objective,
    device=device,
    n_estimators=n_estimators,
    learning_rate=learning_rate,
    num_leaves=num_leaves,
    max_depth=max_depth,
    min_child_samples=min_child_samples,
    subsample=subsample,
    colsample_bytree=colsample_bytree,
    reg_alpha=reg_alpha,
    reg_lambda=reg_lambda,
    random_state=random_state,
    verbose=verbose,
  )


# Save the split settings and feature layout used for inference later.
def save_metadata(
  metadata_path: Path,
  data_path: Path,
  train_end: pd.Timestamp,
  val_end: pd.Timestamp,
  row_count: int,
  feature_columns: list[str],
  sequence_length: int,
  forecast_horizon: int,
) -> None:
  """Persist metadata required for downstream LightGBM inference.

  Args:
    metadata_path: Metadata output path.
    data_path: Source data path used for training.
    train_end: End timestamp of training split.
    val_end: End timestamp of validation split.
    row_count: Number of engineered feature rows.
    feature_columns: Ordered feature columns.
    sequence_length: Sequence length used for lag feature generation.
    forecast_horizon: Forecast horizon used for target alignment.
  """
  metadata_path.parent.mkdir(parents=True, exist_ok=True)
  metadata = {
    "data_path": str(data_path),
    "feature_columns": feature_columns,
    "target_column": TARGET_COLUMN,
    "sequence_length": sequence_length,
    "forecast_horizon": forecast_horizon,
    "train_end": train_end.isoformat(),
    "val_end": val_end.isoformat(),
    "row_count_after_features": row_count,
    "categorical_features": ["scats_number", "location"],
  }
  metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


# Build the movement-level tabular splits from the shared data loader.
def prepare_datasets(data_path: Path, sequence_length: int, forecast_horizon: int) -> tuple[
  pd.DataFrame,
  list[str],
  pd.DataFrame,
  pd.DataFrame,
  pd.DataFrame,
  pd.Timestamp,
  pd.Timestamp,
]:
  """Build movement-level tabular splits from shared loader logic.

  Args:
    data_path: Path to processed input CSV.
    sequence_length: Sequence length used for lag feature generation.
    forecast_horizon: Forecast horizon used for target alignment.

  Returns:
    Prepared tabular dataset bundle from data_loader.
  """
  return prepare_tabular_data(str(data_path), sequence_length, forecast_horizon)


# Select one representative movement slice so the saved plot stays readable.
def build_plot_slice(
  test_df: pd.DataFrame,
  predictions: Any,
  max_points: int = 400,
) -> tuple[np.ndarray, np.ndarray, str]:
  """Build one representative timeseries slice for plotting.

  Args:
    test_df: Test dataframe aligned to predictions.
    predictions: Predicted values in test order.
    max_points: Maximum points to include in saved chart.

  Returns:
    Actual array, predicted array, and chart title.
  """
  plot_df = test_df[["movement_id", "datetime", TARGET_COLUMN]].copy()
  plot_df["predicted"] = predictions

  representative_movement = plot_df["movement_id"].value_counts().idxmax()
  movement_plot_df = (
    plot_df[plot_df["movement_id"] == representative_movement]
    .sort_values("datetime")
    .head(max_points)
  )

  title = f"LightGBM Predictions - {representative_movement}"
  actual = movement_plot_df[TARGET_COLUMN].to_numpy(dtype=float)
  predicted = movement_plot_df["predicted"].to_numpy(dtype=float)
  return actual, predicted, title


# Train the LightGBM model and save model, metadata, metrics, and graph.
def train_lightgbm_model(
  data_path: Path = DATA_PATH,
  trained_models_dir: Path = TRAINED_MODELS_DIR,
  metrics_dir: Path = METRICS_DIR,
  graphs_dir: Path = GRAPHS_DIR,
  model_path: Path = MODEL_PATH,
  metadata_path: Path = METADATA_PATH,
  metrics_path: Path = METRICS_PATH,
  sequence_length: int = DEFAULT_SEQUENCE_LENGTH,
  forecast_horizon: int = DEFAULT_FORECAST_HORIZON,
  objective: str = DEFAULT_OBJECTIVE,
  device: str = DEFAULT_DEVICE,
  n_estimators: int = DEFAULT_N_ESTIMATORS,
  learning_rate: float = DEFAULT_LEARNING_RATE,
  num_leaves: int = DEFAULT_NUM_LEAVES,
  max_depth: int = DEFAULT_MAX_DEPTH,
  min_child_samples: int = DEFAULT_MIN_CHILD_SAMPLES,
  subsample: float = DEFAULT_SUBSAMPLE,
  colsample_bytree: float = DEFAULT_COLSAMPLE_BYTREE,
  reg_alpha: float = DEFAULT_REG_ALPHA,
  reg_lambda: float = DEFAULT_REG_LAMBDA,
  random_state: int = DEFAULT_RANDOM_STATE,
  verbose: int = DEFAULT_VERBOSE,
  eval_metric: str = DEFAULT_EVAL_METRIC,
  early_stopping_rounds: int = DEFAULT_EARLY_STOPPING_ROUNDS,
) -> tuple[LGBMRegressor, dict[str, dict[str, float]]]:
  """Train and persist a LightGBM model and related artifacts.

  Args:
    data_path: Input processed dataset path.
    trained_models_dir: Directory for serialized model artifacts.
    metrics_dir: Directory for metric JSON outputs.
    graphs_dir: Directory for generated charts.
    model_path: Destination LightGBM model path.
    metadata_path: Destination metadata JSON path.
    metrics_path: Destination metrics JSON path.
    sequence_length: Sequence length used during tabular feature generation.
    forecast_horizon: Forecast horizon used during target alignment.
    objective: LightGBM objective.
    device: LightGBM compute device.
    n_estimators: Maximum boosting rounds.
    learning_rate: Boosting learning rate.
    num_leaves: Maximum number of leaves.
    max_depth: Maximum tree depth.
    min_child_samples: Minimum child sample count.
    subsample: Row sampling ratio.
    colsample_bytree: Feature sampling ratio.
    reg_alpha: L1 regularization strength.
    reg_lambda: L2 regularization strength.
    random_state: Random seed.
    verbose: Model verbosity.
    eval_metric: Validation metric for early stopping.
    early_stopping_rounds: Early-stopping patience.

  Returns:
    Trained model and split metrics dictionary.
  """
  trained_models_dir.mkdir(parents=True, exist_ok=True)
  metrics_dir.mkdir(parents=True, exist_ok=True)
  graphs_dir.mkdir(parents=True, exist_ok=True)

  LOGGER.info("Preparing tabular datasets from %s", data_path)
  feature_df, feature_columns, train_df, val_df, test_df, train_end, val_end = prepare_datasets(
    data_path,
    sequence_length,
    forecast_horizon,
  )
  x_train, y_train = get_xy(train_df, feature_columns)
  x_val, y_val = get_xy(val_df, feature_columns)
  x_test, y_test = get_xy(test_df, feature_columns)

  model = create_model(
    objective=objective,
    device=device,
    n_estimators=n_estimators,
    learning_rate=learning_rate,
    num_leaves=num_leaves,
    max_depth=max_depth,
    min_child_samples=min_child_samples,
    subsample=subsample,
    colsample_bytree=colsample_bytree,
    reg_alpha=reg_alpha,
    reg_lambda=reg_lambda,
    random_state=random_state,
    verbose=verbose,
  )
  LOGGER.info("Training LightGBM model")
  model.fit(
    x_train,
    y_train,
    eval_set=[(x_val, y_val)],
    eval_metric=eval_metric,
    callbacks=[early_stopping(early_stopping_rounds, verbose=False)],
  )

  LOGGER.info("Running validation and test inference")
  val_predictions = predict_tabular_model(model, val_df, feature_columns)
  test_predictions = predict_tabular_model(model, test_df, feature_columns)
  val_metrics = evaluate_tabular_predictions(y_val.to_numpy(dtype=float), val_predictions)
  test_metrics = evaluate_tabular_predictions(y_test.to_numpy(dtype=float), test_predictions)

  model_path.parent.mkdir(parents=True, exist_ok=True)
  model.booster_.save_model(str(model_path))
  LOGGER.info("Saved model artifact to %s", model_path)

  save_metadata(
    metadata_path=metadata_path,
    data_path=data_path,
    train_end=train_end,
    val_end=val_end,
    row_count=len(feature_df),
    feature_columns=feature_columns,
    sequence_length=sequence_length,
    forecast_horizon=forecast_horizon,
  )
  metrics_path.parent.mkdir(parents=True, exist_ok=True)
  metrics_path.write_text(
    json.dumps({"validation": val_metrics, "test": test_metrics}, indent=2),
    encoding="utf-8",
  )
  LOGGER.info("Saved metrics to %s", metrics_path)

  plot_actual, plot_predicted, plot_title = build_plot_slice(test_df, test_predictions)
  saved_plot = plot_predictions(
    plot_actual,
    plot_predicted,
    plot_title,
    output_dir=graphs_dir,
    filename="lightgbm_predictions.png",
  )
  LOGGER.info("Saved test prediction plot to %s", saved_plot)

  return model, {"validation": val_metrics, "test": test_metrics}


# Run end-to-end training from the command line.
def main() -> None:
  """CLI entrypoint for explicit LightGBM training."""
  logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
  parser = argparse.ArgumentParser(description="Train LightGBM model artifacts.")
  parser.add_argument(
    "--data-path",
    default=str(DATA_PATH),
    help="Path to processed training data.",
  )
  args = parser.parse_args()

  LOGGER.info("Training LightGBM model")
  _, metrics = train_lightgbm_model(data_path=Path(args.data_path))
  LOGGER.info("Validation metrics: %s", metrics["validation"])
  LOGGER.info("Test metrics: %s", metrics["test"])


if __name__ == "__main__":
  main()
