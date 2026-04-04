"""Execute filtered evaluation tests against prepared prediction artifacts."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import logging
from pathlib import Path

import pandas as pd

from src.evaluation import MetricDict, compute_metrics, plot_predictions
from src.models.gru_model import train_gru_model
from src.models.lstm_model import train_lstm_model
from src.test_filters import get_test_cases, get_test_filter

LOGGER = logging.getLogger(__name__)

SRC_ROOT: Path = Path(__file__).resolve().parent
PROCESSED_2006_PATH: Path = SRC_ROOT / "data" / "processed" / "2006_processed.csv"
PREDICTIONS_DIR: Path = SRC_ROOT / "results" / "predictions"
RESULTS_DIR: Path = SRC_ROOT / "results" / "test_results"
GRAPH_DIR: Path = SRC_ROOT / "results" / "test_graphs"
AVAILABLE_MODELS: list[str] = ["lstm", "gru", "lightgbm"]


@dataclass(frozen=True)
class SingleTestResult:
  """Container for one test-case execution result."""

  test_id: str
  n_samples: int
  data_key: str
  metrics: dict[str, MetricDict]


def train_sequence_models_for_tests(data_path: Path = PROCESSED_2006_PATH) -> None:
  """Train LSTM and GRU models explicitly for test workflows.

  Args:
    data_path: Path to processed training data.
  """
  LOGGER.info("Starting explicit LSTM training for tests")
  train_lstm_model(data_path=data_path)
  LOGGER.info("Starting explicit GRU training for tests")
  train_gru_model(data_path=data_path)


def get_metrics_csv_path(data_key: str) -> Path:
  """Return metrics CSV path for a dataset key.

  Args:
    data_key: Dataset identifier.

  Returns:
    Output path for aggregated metric CSV.
  """
  return RESULTS_DIR / f"test_metrics_full_{data_key}.csv"


def run_single_test(test_name: str, data_key: str = "2014", model_filter: str = "all") -> SingleTestResult:
  """Run one test case and return structured metrics.

  Args:
    test_name: Test identifier or test name.
    data_key: Dataset key used for prediction artifact lookup.
    model_filter: One model name or all.

  Returns:
    Structured single-test result.

  Raises:
    FileNotFoundError: If required prediction file is missing.
    ValueError: If filtering yields zero rows.
    KeyError: If expected prediction columns are missing.
  """
  predictions_path = PREDICTIONS_DIR / f"{data_key}_predictions.csv"
  if not predictions_path.exists():
    raise FileNotFoundError(
      f"Prediction artifact not found: {predictions_path}. Run python -m src.predict --data {data_key} first."
    )

  LOGGER.info("Loading predictions from %s", predictions_path)
  df = pd.read_csv(predictions_path, parse_dates=["datetime"])
  df["datetime"] = pd.to_datetime(df["datetime"], format="ISO8601", errors="raise")

  filtered = get_test_filter(test_name, df)
  if filtered.empty:
    raise ValueError(f"No rows matched test filter '{test_name}'.")

  n_samples = len(filtered)
  LOGGER.info("Test '%s' produced %d rows after filtering", test_name, n_samples)
  models_to_eval = AVAILABLE_MODELS if model_filter == "all" else [model_filter.lower()]

  RESULTS_DIR.mkdir(parents=True, exist_ok=True)
  GRAPH_DIR.mkdir(parents=True, exist_ok=True)

  test_metrics: dict[str, MetricDict] = {}
  for model_name in models_to_eval:
    pred_col = f"predicted_{model_name}"
    if pred_col not in filtered.columns:
      raise KeyError(f"Prediction column '{pred_col}' is missing from {predictions_path}.")

    actual = filtered["actual"].to_numpy(dtype=float)
    predicted = filtered[pred_col].to_numpy(dtype=float)
    metrics = compute_metrics(actual, predicted)
    test_metrics[model_name] = metrics

    LOGGER.info("%s on %s -> MAE: %.4f, RMSE: %.4f, MAPE: %.4f%%", model_name.upper(), test_name, metrics["MAE"], metrics["RMSE"], metrics["MAPE"])

    test_graph_dir = GRAPH_DIR / test_name
    plot_predictions(
      actual,
      predicted,
      title=f"{model_name.upper()} - {test_name} ({data_key})",
      output_dir=test_graph_dir,
      filename=f"{model_name}_predictions.png",
    )

  if not test_metrics:
    raise RuntimeError(f"No model metrics were generated for test '{test_name}'.")

  return SingleTestResult(
    test_id=test_name,
    n_samples=n_samples,
    data_key=data_key,
    metrics=test_metrics,
  )


def run_all_tests(data_key: str = "2014") -> pd.DataFrame:
  """Run all configured test cases and return aggregated metrics.

  Args:
    data_key: Dataset key used for prediction artifact lookup.

  Returns:
    Aggregated metrics dataframe.

  Raises:
    RuntimeError: If no metrics rows were generated.
  """
  LOGGER.info("Running all test cases on %s dataset", data_key)
  csv_rows: list[dict[str, object]] = []

  for test_case in get_test_cases():
    test_id = str(test_case["id"])
    LOGGER.info("Running %s: %s", test_id, test_case["description"])

    result = run_single_test(test_id, data_key=data_key)
    if not result.metrics:
      raise RuntimeError(f"Test '{test_id}' returned empty metrics; aborting to avoid silent continuation.")

    for model_name, metrics in result.metrics.items():
      csv_rows.append(
        {
          "test_id": test_id,
          "data_key": data_key,
          "model": model_name.upper(),
          "n_samples": result.n_samples,
          "mae": metrics["MAE"],
          "rmse": metrics["RMSE"],
          "mape": metrics["MAPE"],
        }
      )

  if not csv_rows:
    raise RuntimeError("All tests produced no metric rows; failing explicitly.")

  results_df = pd.DataFrame(csv_rows)
  metrics_csv_path = get_metrics_csv_path(data_key)
  metrics_csv_path.parent.mkdir(parents=True, exist_ok=True)
  results_df.to_csv(metrics_csv_path, index=False)
  LOGGER.info("Test metrics saved to %s", metrics_csv_path)

  for model in AVAILABLE_MODELS:
    model_results = results_df[results_df["model"] == model.upper()][["test_id", "n_samples", "mae", "rmse", "mape"]]
    LOGGER.info("Summary for %s model:\n%s", model.upper(), model_results.to_string(index=False))

  return results_df


def main() -> int:
  """CLI entrypoint for filtered test execution.

  Returns:
    Process exit code.
  """
  logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
  parser = argparse.ArgumentParser(description="Run filtered tests over prediction artifacts.")
  parser.add_argument(
    "--test",
    default=None,
    help="Test case id/name (for example, T01). If omitted, runs all tests.",
  )
  parser.add_argument(
    "--model",
    default="all",
    choices=AVAILABLE_MODELS + ["all"],
    help="Model to evaluate.",
  )
  parser.add_argument("--data", default="2014", choices=["2006", "2014"], help="Predictions dataset key.")
  parser.add_argument(
    "--train-sequence-models",
    action="store_true",
    help="Explicitly train LSTM and GRU models before running tests.",
  )
  args = parser.parse_args()

  if args.train_sequence_models:
    train_sequence_models_for_tests()

  if args.test:
    test_name = Path(args.test).stem
    result = run_single_test(test_name, data_key=args.data, model_filter=args.model)
    LOGGER.info("Completed single test '%s' with %d samples", result.test_id, result.n_samples)
  else:
    run_all_tests(data_key=args.data)

  return 0


if __name__ == "__main__":
  raise SystemExit(main())
