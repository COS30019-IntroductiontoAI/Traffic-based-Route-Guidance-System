"""Evaluation utilities for sequence and tabular traffic models."""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lightgbm import Booster
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.config.model_config import FORECAST_HORIZON, SEQ_LEN
from src.data_loader import prepare_data, prepare_tabular_data
from src.models.gru_model import train_gru_model
from src.models.lstm_model import train_lstm_model
from src.models.model_loader import load_keras_model
from src.predict import MODEL_SPECS, predict_tabular_model

LOGGER = logging.getLogger(__name__)

MetricDict = dict[str, float]

SRC_ROOT: Path = Path(__file__).resolve().parent
GRAPH_DIR: Path = SRC_ROOT / "results" / "graphs"
METRICS_DIR: Path = SRC_ROOT / "results" / "metrics"
PROCESSED_2006_PATH: Path = SRC_ROOT / "data" / "processed" / "2006_processed.csv"


@dataclass(frozen=True)
class SequenceContext:
  """Container for sequence-model evaluation arrays and scaler."""

  validation: tuple[np.ndarray, np.ndarray]
  test: tuple[np.ndarray, np.ndarray]
  scaler: Any


@dataclass(frozen=True)
class TabularContext:
  """Container for tabular-model evaluation splits and metadata."""

  validation: pd.DataFrame
  test: pd.DataFrame
  feature_columns: list[str]
  train_end: pd.Timestamp
  val_end: pd.Timestamp


@dataclass(frozen=True)
class EvaluationContext:
  """Container for all evaluation contexts used by model families."""

  sequence: SequenceContext
  tabular: TabularContext


def train_sequence_models_for_evaluation(data_path: Path = PROCESSED_2006_PATH) -> None:
  """Train LSTM and GRU models explicitly for evaluation workflows.

  Args:
    data_path: Path to processed training data.
  """
  LOGGER.info("Starting explicit LSTM training for evaluation")
  train_lstm_model(data_path=data_path)
  LOGGER.info("Starting explicit GRU training for evaluation")
  train_gru_model(data_path=data_path)


def inverse_transform(scaler: Any, data: np.ndarray) -> np.ndarray:
  """Inverse-transform scaled sequence values back to traffic-volume space.

  Args:
    scaler: Scaler used to normalize model targets.
    data: Array of scaled values.

  Returns:
    Values in original traffic-volume scale.
  """
  flat = data.flatten()
  dummy = np.zeros((len(flat), scaler.n_features_in_))
  dummy[:, 0] = flat
  inversed = scaler.inverse_transform(dummy)[:, 0]
  return np.expm1(inversed)


def compute_metrics(actual: np.ndarray, predicted: np.ndarray) -> MetricDict:
  """Compute MAE, RMSE, and MAPE with a safe MAPE zero-denominator guard.

  Args:
    actual: Ground-truth values.
    predicted: Predicted values aligned to actual.

  Returns:
    Metric dictionary with keys MAE, RMSE, and MAPE.

  Raises:
    ValueError: If arrays are empty or have mismatched shapes.
  """
  if actual.size == 0 or predicted.size == 0:
    raise ValueError("Metric computation requires non-empty actual and predicted arrays.")
  if actual.shape != predicted.shape:
    raise ValueError("Actual and predicted arrays must have identical shapes.")

  mae = mean_absolute_error(actual, predicted)
  rmse = float(np.sqrt(mean_squared_error(actual, predicted)))

  non_zero_mask = actual != 0
  if not np.any(non_zero_mask):
    LOGGER.warning("All actual values are zero; setting MAPE to 0.0 to avoid undefined computation.")
    mape = 0.0
  else:
    actual_masked = actual[non_zero_mask]
    predicted_masked = predicted[non_zero_mask]
    mape = float(np.mean(np.abs((actual_masked - predicted_masked) / actual_masked)) * 100.0)

  return {"MAE": float(mae), "RMSE": rmse, "MAPE": mape}


def evaluate_sequence_model(
  model_path: str | Path,
  x_split: np.ndarray,
  y_split: np.ndarray,
  scaler: Any,
) -> tuple[np.ndarray, np.ndarray, MetricDict]:
  """Evaluate a saved sequence model on one split.

  Args:
    model_path: Path to the saved Keras model artifact.
    x_split: Input feature tensor.
    y_split: Ground-truth target tensor.
    scaler: Scaler used for target normalization.

  Returns:
    Tuple of inverse-transformed actual values, predictions, and metrics.
  """
  model = load_keras_model(model_path)
  predictions = model.predict(x_split, verbose=0)

  actual_real = inverse_transform(scaler, y_split)
  predicted_real = inverse_transform(scaler, predictions.flatten())
  metrics = compute_metrics(actual_real, predicted_real)
  return actual_real, predicted_real, metrics


def evaluate_model(
  model_path: str | Path,
  x_split: np.ndarray,
  y_split: np.ndarray,
  scaler: Any,
) -> tuple[np.ndarray, np.ndarray, MetricDict]:
  """Backward-compatible alias for sequence model evaluation."""
  return evaluate_sequence_model(model_path, x_split, y_split, scaler)


def plot_predictions(
  actual: np.ndarray,
  predicted: np.ndarray,
  title: str,
  output_dir: Path = GRAPH_DIR,
  filename: str | None = None,
) -> Path:
  """Save actual-vs-predicted comparison chart.

  Args:
    actual: Ground-truth values.
    predicted: Predicted values.
    title: Chart title.
    output_dir: Directory for saved plot files.
    filename: Optional filename override.

  Returns:
    Saved plot path.
  """
  output_dir.mkdir(parents=True, exist_ok=True)
  save_name = filename or f"{title.lower().replace(' ', '_')}.png"
  save_path = output_dir / save_name

  plt.figure(figsize=(14, 5))
  plt.plot(actual[:400], label="Actual", color="blue")
  plt.plot(predicted[:400], label="Predicted", color="orange")
  plt.title(title)
  plt.xlabel("Time Steps")
  plt.ylabel("Traffic Volume")
  plt.legend()
  plt.savefig(save_path, bbox_inches="tight")
  plt.close()
  return save_path


def evaluate_tabular_predictions(actual: np.ndarray, predicted: np.ndarray) -> MetricDict:
  """Compute tabular metrics from already-produced predictions."""
  return compute_metrics(actual, predicted)


def evaluate_tabular_model(
  model: Booster,
  split_df: pd.DataFrame,
  feature_columns: list[str],
  target_column: str = "traffic_volume",
) -> tuple[np.ndarray, np.ndarray, MetricDict]:
  """Evaluate one tabular model on one dataframe split.

  Args:
    model: Loaded LightGBM booster.
    split_df: Split dataframe for evaluation.
    feature_columns: Feature column names expected by the model.
    target_column: Name of target column.

  Returns:
    Tuple of actual values, predicted values, and metrics.
  """
  actual = split_df[target_column].to_numpy(dtype=float)
  predicted = predict_tabular_model(model, split_df, feature_columns)
  metrics = evaluate_tabular_predictions(actual, predicted)
  return actual, predicted, metrics


def build_evaluation_context() -> EvaluationContext:
  """Build shared validation/test contexts for sequence and tabular models.

  Returns:
    EvaluationContext containing all split arrays and dataframes.
  """
  (_, _), (x_val, y_val), (x_test, y_test), scaler, _label_encoder = prepare_data(
    filepath=str(PROCESSED_2006_PATH),
    seq_len=SEQ_LEN,
    forecast_horizon=FORECAST_HORIZON,
  )
  _, feature_columns, _, val_df, test_df, train_end, val_end = prepare_tabular_data(
    filepath=str(PROCESSED_2006_PATH),
    seq_len=SEQ_LEN,
    forecast_horizon=FORECAST_HORIZON,
  )
  return EvaluationContext(
    sequence=SequenceContext(
      validation=(x_val, y_val),
      test=(x_test, y_test),
      scaler=scaler,
    ),
    tabular=TabularContext(
      validation=val_df,
      test=test_df,
      feature_columns=feature_columns,
      train_end=pd.Timestamp(train_end),
      val_end=pd.Timestamp(val_end),
    ),
  )


def evaluate_model_spec(spec: dict[str, Any], context: EvaluationContext, graph_dir: Path) -> dict[str, MetricDict]:
  """Evaluate a model spec on validation and test splits.

  Args:
    spec: Model specification entry from MODEL_SPECS.
    context: Shared evaluation data context.
    graph_dir: Directory for generated comparison plots.

  Returns:
    Dictionary keyed by split name with metric dictionaries.
  """
  metrics_bundle: dict[str, MetricDict] = {}
  model_name = str(spec["name"]).upper()

  if spec["kind"] == "sequence":
    for split_name, split in {
      "validation": context.sequence.validation,
      "test": context.sequence.test,
    }.items():
      x_split, y_split = split
      actual, predicted, split_metrics = evaluate_sequence_model(spec["path"], x_split, y_split, context.sequence.scaler)
      metrics_bundle[split_name] = split_metrics

      if split_name == "test":
        plot_path = plot_predictions(
          actual,
          predicted,
          title=f"{model_name} Predictions ({split_name})",
          output_dir=graph_dir,
          filename=f"{str(spec['name'])}_{split_name}_predictions.png",
        )
        LOGGER.info("%s %s plot saved to %s", model_name, split_name, plot_path)

      LOGGER.info("%s %s MAE: %.4f", model_name, split_name, split_metrics["MAE"])
      LOGGER.info("%s %s RMSE: %.4f", model_name, split_name, split_metrics["RMSE"])
      LOGGER.info("%s %s MAPE: %.4f%%", model_name, split_name, split_metrics["MAPE"])
    return metrics_bundle

  if spec["kind"] == "tabular":
    model = Booster(model_file=str(spec["path"]))
    for split_name, split_df in {
      "validation": context.tabular.validation,
      "test": context.tabular.test,
    }.items():
      actual, predicted, split_metrics = evaluate_tabular_model(model, split_df, context.tabular.feature_columns)
      metrics_bundle[split_name] = split_metrics

      if split_name == "test":
        plot_path = plot_predictions(
          actual,
          predicted,
          title=f"{model_name} Predictions ({split_name})",
          output_dir=graph_dir,
          filename=f"{str(spec['name'])}_{split_name}_predictions.png",
        )
        LOGGER.info("%s %s plot saved to %s", model_name, split_name, plot_path)

      LOGGER.info("%s %s MAE: %.4f", model_name, split_name, split_metrics["MAE"])
      LOGGER.info("%s %s RMSE: %.4f", model_name, split_name, split_metrics["RMSE"])
      LOGGER.info("%s %s MAPE: %.4f%%", model_name, split_name, split_metrics["MAPE"])
    return metrics_bundle

  LOGGER.warning("Unsupported model kind '%s' for model '%s'", spec.get("kind"), spec.get("name"))
  return metrics_bundle


def save_metrics_json(model_name: str, metrics: dict[str, MetricDict], output_dir: Path = METRICS_DIR) -> Path:
  """Save metrics to JSON file.

  Args:
    model_name: Logical model name.
    metrics: Metrics dictionary keyed by split.
    output_dir: Output directory for metrics files.

  Returns:
    Path to saved JSON file.
  """
  output_dir.mkdir(parents=True, exist_ok=True)
  metrics_path = output_dir / f"{model_name.lower()}_metrics.json"
  with metrics_path.open("w", encoding="utf-8") as fp:
    json.dump(metrics, fp, indent=2)
  return metrics_path


def evaluate_saved_models(
  graph_dir: Path = GRAPH_DIR,
  metrics_dir: Path = METRICS_DIR,
  train_sequence_models: bool = False,
) -> None:
  """Evaluate all model artifacts and persist plots/metrics.

  Args:
    graph_dir: Directory for prediction comparison plots.
    metrics_dir: Directory for metric json files.
    train_sequence_models: Whether to train LSTM/GRU explicitly before evaluation.
  """
  if train_sequence_models:
    train_sequence_models_for_evaluation(PROCESSED_2006_PATH)

  LOGGER.info("Loading validation and test data")
  context = build_evaluation_context()
  x_val, y_val = context.sequence.validation
  x_test, y_test = context.sequence.test
  LOGGER.info("X_val shape: %s", x_val.shape)
  LOGGER.info("y_val shape: %s", y_val.shape)
  LOGGER.info("X_test shape: %s", x_test.shape)
  LOGGER.info("y_test shape: %s", y_test.shape)
  LOGGER.info("LightGBM train_end: %s", context.tabular.train_end)
  LOGGER.info("LightGBM val_end: %s", context.tabular.val_end)

  for spec in MODEL_SPECS:
    spec_path = Path(spec["path"])
    if not spec_path.exists():
      LOGGER.warning("Skipping %s evaluation; artifact is missing at %s", str(spec["name"]).upper(), spec_path)
      continue

    LOGGER.info("Evaluating %s model", str(spec["name"]).upper())
    metrics_bundle = evaluate_model_spec(spec, context, graph_dir)
    metrics_path = save_metrics_json(str(spec["name"]).upper(), metrics_bundle, output_dir=metrics_dir)
    LOGGER.info("Saved metrics to %s", metrics_path)

  LOGGER.info("Evaluation completed")


def main() -> int:
  """CLI entrypoint for model evaluation.

  Returns:
    Process exit code.
  """
  logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
  parser = argparse.ArgumentParser(description="Evaluate saved model artifacts.")
  parser.add_argument(
    "--train-sequence-models",
    action="store_true",
    help="Explicitly train LSTM and GRU models before evaluation.",
  )
  args = parser.parse_args()

  evaluate_saved_models(train_sequence_models=bool(args.train_sequence_models))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
