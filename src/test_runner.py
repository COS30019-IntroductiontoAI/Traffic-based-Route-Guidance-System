import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.evaluation import plot_predictions, compute_metrics
from src.test_filters import get_test_filter, get_test_cases

SRC_ROOT = Path(__file__).resolve().parent
PREDICTIONS_DIR = SRC_ROOT / "results" / "predictions"
RESULTS_DIR = SRC_ROOT / "results" / "test_results"
GRAPH_DIR = SRC_ROOT / "results" / "test_graphs"
AVAILABLE_MODELS = ["lstm", "gru", "lightgbm"]


def get_metrics_csv_path(data_key: str) -> Path:
  """Get the metrics CSV path for a given dataset."""
  return RESULTS_DIR / f"test_metrics_full_{data_key}.csv"


def run_single_test(test_name: str, data_key: str = "2014", model_filter: str = "all") -> dict:
  """Run a single test case and return metrics dictionary."""
  predictions_path = PREDICTIONS_DIR / f"{data_key}_predictions.csv"
  
  if not predictions_path.exists():
    print(f"Error: '{predictions_path}' not found. Run predict.py --data {data_key} first.")
    return {}

  print(f"Loading predictions from {predictions_path}...")
  df = pd.read_csv(predictions_path, parse_dates=["datetime"])
  
  # Ensure datetime is properly converted
  df["datetime"] = pd.to_datetime(df["datetime"], format='ISO8601')
  
  filtered = get_test_filter(test_name, df)

  if len(filtered) == 0:
    print(f"Error: No data found after applying filter for '{test_name}'.")
    return {}

  n_samples = len(filtered)
  print(f"Test case '{test_name}': {n_samples} rows after filtering.")
  models_to_eval = AVAILABLE_MODELS if model_filter == "all" else [model_filter.lower()]

  RESULTS_DIR.mkdir(parents=True, exist_ok=True)
  GRAPH_DIR.mkdir(parents=True, exist_ok=True)
  
  test_results = {}
  
  for model_name in models_to_eval:
    pred_col = f"predicted_{model_name}"
    if pred_col not in filtered.columns:
      print(f"Error: Column '{pred_col}' not found in predictions CSV. Skipping.")
      continue

    actual = filtered["actual"].values
    predicted = filtered[pred_col].values
    metrics = compute_metrics(actual, predicted)
    test_results[model_name] = metrics

    print(f"\n{model_name.upper()} results on {test_name}:")
    print(f"  MAE  : {metrics['MAE']:.4f}")
    print(f"  RMSE : {metrics['RMSE']:.4f}")
    print(f"  MAPE : {metrics['MAPE']:.4f}%")

    # Generate comparison plot for test set, organized by test case subfolder
    test_graph_dir = GRAPH_DIR / test_name
    plot_predictions(
      actual,
      predicted,
      title=f"{model_name.upper()} - {test_name} ({data_key})",
      output_dir=test_graph_dir,
      filename=f"{model_name}_predictions.png",
      show=False,
    )
  
  return {
    "test_id": test_name,
    "n_samples": n_samples,
    "data_key": data_key,
    "metrics": test_results
  }


def run_all_tests(data_key: str = "2014") -> pd.DataFrame:
  """Run all 10 test cases and return aggregated metrics as DataFrame."""
  print(f"\n{'='*80}")
  print(f"Running All 10 Test Cases on {data_key} Dataset")
  print(f"{'='*80}\n")
  
  csv_rows = []
  
  for test_case in get_test_cases():
    test_id = test_case["id"]
    print(f"\n--- {test_id}: {test_case['description']} ---")
    
    result = run_single_test(test_id, data_key=data_key)
    
    if not result:
      continue
    
    for model_name, metrics in result["metrics"].items():
      csv_rows.append({
        "test_id": test_id,
        "data_key": data_key,
        "model": model_name.upper(),
        "n_samples": result["n_samples"],
        "mae": metrics["MAE"],
        "rmse": metrics["RMSE"],
        "mape": metrics["MAPE"],
      })
  
  # Save results to CSV
  results_df = pd.DataFrame(csv_rows)
  metrics_csv_path = get_metrics_csv_path(data_key)
  results_df.to_csv(metrics_csv_path, index=False)
  print(f"\n✓ Test metrics saved -> {metrics_csv_path}")
  
  # Print summary table
  print(f"\n{'='*80}")
  print(f"SUMMARY: All Test Cases on {data_key} Dataset")
  print(f"{'='*80}")
  
  # Pivot for nice display
  for model in AVAILABLE_MODELS:
    print(f"\n{model.upper()} Model Results:")
    model_results = results_df[results_df["model"] == model.upper()].copy()
    model_results = model_results[["test_id", "n_samples", "mae", "rmse", "mape"]]
    print(model_results.to_string(index=False))
  
  return results_df


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--test",
    default=None,
    help="Test case name (e.g., T01). If omitted, runs all 10 tests.",
  )
  parser.add_argument(
    "--model",
    default="all",
    choices=AVAILABLE_MODELS + ["all"],
    help="Model to evaluate",
  )
  parser.add_argument("--data", default="2014", choices=["2006", "2014"], help="Predictions dataset to use")
  args = parser.parse_args()

  if args.test:
    # Run single test
    test_name = Path(args.test).stem
    run_single_test(test_name, data_key=args.data, model_filter=args.model)
  else:
    # Run all tests and aggregate to CSV
    run_all_tests(data_key=args.data)


if __name__ == "__main__":
  main()
