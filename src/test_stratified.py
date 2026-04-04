"""Run stratified tests on the held-out 2006 split using prepared predictions."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from src.config.model_config import FORECAST_HORIZON, SEQ_LEN
from src.data_loader import prepare_tabular_data
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
METRICS_CSV_PATH: Path = RESULTS_DIR / "test_split_metrics.csv"
AVAILABLE_MODELS: list[str] = ["lstm", "gru", "lightgbm"]


@dataclass(frozen=True)
class StratifiedTestRow:
    """Aggregated metrics row for one test-case/model pair."""

    test_id: str
    test_name: str
    model: str
    n_samples: int
    mae: float
    rmse: float
    mape: float


def train_sequence_models_for_tests(data_path: Path = PROCESSED_2006_PATH) -> None:
    """Train LSTM and GRU models explicitly for stratified test workflows.

    Args:
        data_path: Path to processed training data.
    """
    LOGGER.info("Starting explicit LSTM training for stratified tests")
    train_lstm_model(data_path=data_path)
    LOGGER.info("Starting explicit GRU training for stratified tests")
    train_gru_model(data_path=data_path)


def extract_test_split_predictions() -> pd.DataFrame:
    """Extract 20 percent held-out split rows from full 2006 prediction artifact.

    Returns:
        Dataframe containing only rows in the test split period.

    Raises:
        FileNotFoundError: If full prediction artifact is missing.
        ValueError: If extracted split is empty.
    """
    _, _, _, _, _test_df, _train_end, val_end = prepare_tabular_data(
        filepath=str(PROCESSED_2006_PATH),
        seq_len=SEQ_LEN,
        forecast_horizon=FORECAST_HORIZON,
    )

    full_predictions_path = PREDICTIONS_DIR / "2006_predictions.csv"
    if not full_predictions_path.exists():
        raise FileNotFoundError(
            f"Full predictions not found at {full_predictions_path}. Run python -m src.predict --data 2006 first."
        )

    LOGGER.info("Loading full predictions from %s", full_predictions_path)
    full_predictions = pd.read_csv(full_predictions_path, parse_dates=["datetime"])
    full_predictions["datetime"] = pd.to_datetime(full_predictions["datetime"], format="ISO8601", errors="raise")

    test_split_predictions = full_predictions[full_predictions["datetime"] > val_end].copy()
    if test_split_predictions.empty:
        raise ValueError("No rows were extracted for the 2006 stratified test split.")

    LOGGER.info(
        "Extracted %d test-split rows out of %d total rows",
        len(test_split_predictions),
        len(full_predictions),
    )
    LOGGER.info(
        "Test split date range: %s to %s",
        test_split_predictions["datetime"].min(),
        test_split_predictions["datetime"].max(),
    )
    return test_split_predictions


def save_test_split_predictions(test_predictions: pd.DataFrame) -> Path:
    """Persist extracted test split predictions to disk.

    Args:
        test_predictions: Test split predictions dataframe.

    Returns:
        Output path of saved CSV.
    """
    output_path = PREDICTIONS_DIR / "2006_test_split_predictions.csv"
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
    test_predictions.to_csv(output_path, index=False)
    LOGGER.info("Test split predictions saved to %s", output_path)
    return output_path


def run_stratified_tests(test_predictions: pd.DataFrame | None = None) -> dict[str, dict[str, Any]]:
    """Run all test filters on the 2006 test split predictions.

    Args:
        test_predictions: Optional in-memory dataframe. If omitted, loads from disk.

    Returns:
        Nested dictionary keyed by test id and model name.

    Raises:
        FileNotFoundError: If saved test split artifact is missing.
        ValueError: If required filtered rows are empty.
        KeyError: If expected prediction columns are missing.
        RuntimeError: If no metrics rows are generated.
    """
    if test_predictions is None:
        test_predictions_path = PREDICTIONS_DIR / "2006_test_split_predictions.csv"
        if not test_predictions_path.exists():
            raise FileNotFoundError(
                f"Test split predictions not found at {test_predictions_path}. Run extraction first."
            )
        LOGGER.info("Loading test split predictions from %s", test_predictions_path)
        test_predictions = pd.read_csv(test_predictions_path, parse_dates=["datetime"])
        test_predictions["datetime"] = pd.to_datetime(test_predictions["datetime"], format="ISO8601", errors="raise")

    LOGGER.info("Running 10 test cases on 20 percent split (%d rows)", len(test_predictions))

    test_results: dict[str, dict[str, Any]] = {}
    csv_rows: list[StratifiedTestRow] = []

    for test_case in get_test_cases():
        test_id = str(test_case["id"])
        test_name = str(test_case["name"])
        LOGGER.info("Running %s: %s", test_id, test_case["description"])

        filtered_data = get_test_filter(test_id, test_predictions)
        n_samples = len(filtered_data)
        if n_samples == 0:
            raise ValueError(f"No rows matched stratified filter for test '{test_id}'.")

        test_results[test_id] = {"n_samples": n_samples}

        for model_name in AVAILABLE_MODELS:
            pred_col = f"predicted_{model_name}"
            if pred_col not in filtered_data.columns:
                raise KeyError(f"Missing prediction column '{pred_col}' for test '{test_id}'.")

            actual = filtered_data["actual"].to_numpy(dtype=float)
            predicted = filtered_data[pred_col].to_numpy(dtype=float)
            metrics: MetricDict = compute_metrics(actual, predicted)
            test_results[test_id][model_name] = metrics

            LOGGER.info(
                "%s %s -> MAE: %.4f RMSE: %.4f MAPE: %.2f%%",
                test_id,
                model_name.upper(),
                metrics["MAE"],
                metrics["RMSE"],
                metrics["MAPE"],
            )

            csv_rows.append(
                StratifiedTestRow(
                    test_id=test_id,
                    test_name=test_name,
                    model=model_name.upper(),
                    n_samples=n_samples,
                    mae=metrics["MAE"],
                    rmse=metrics["RMSE"],
                    mape=metrics["MAPE"],
                )
            )

            test_graph_dir = GRAPH_DIR / test_id
            plot_predictions(
                actual,
                predicted,
                title=f"{model_name.upper()} - {test_id} (20% test split)",
                output_dir=test_graph_dir,
                filename=f"{model_name}_predictions.png",
            )

    if not csv_rows:
        raise RuntimeError("No stratified metrics were generated.")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    results_df = pd.DataFrame([row.__dict__ for row in csv_rows])
    results_df.to_csv(METRICS_CSV_PATH, index=False)
    LOGGER.info("Stratified test metrics saved to %s", METRICS_CSV_PATH)

    for model in AVAILABLE_MODELS:
        model_results = results_df[results_df["model"] == model.upper()][["test_id", "n_samples", "mae", "rmse", "mape"]]
        LOGGER.info("Summary for %s model:\n%s", model.upper(), model_results.to_string(index=False))

    return test_results


def main() -> int:
    """CLI entrypoint for stratified test evaluation.

    Returns:
        Process exit code.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    parser = argparse.ArgumentParser(description="Run stratified tests on 2006 test split predictions.")
    parser.add_argument(
        "--train-sequence-models",
        action="store_true",
        help="Explicitly train LSTM and GRU models before stratified tests.",
    )
    args = parser.parse_args()

    if args.train_sequence_models:
        train_sequence_models_for_tests()

    test_predictions = extract_test_split_predictions()
    save_test_split_predictions(test_predictions)
    run_stratified_tests(test_predictions)

    LOGGER.info("Stratified testing completed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, KeyError, RuntimeError, pd.errors.ParserError, OSError) as exc:
        LOGGER.error("Error during stratified testing: %s", exc)
        raise SystemExit(1)
