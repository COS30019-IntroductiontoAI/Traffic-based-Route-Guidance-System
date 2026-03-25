import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.evaluation import plot_predictions

PREDICTIONS_DIR = Path("results/predictions")
RESULTS_DIR = Path("results/test_results")
GRAPH_DIR = Path("results/test_graphs")
AVAILABLE_MODELS = ["lstm", "gru", "lightgbm"]

# --------------------------------------
# --- Huy - Shared Scenario Filters  ---
# --------------------------------------

# Return a filtered dataframe for the requested scenario test.
def get_test_filter(test_name, df):
  if test_name in {"T01-morning_peak_hour", "T01"}:
    return df[(df["hour"] >= 7) & (df["hour"] <= 9) & (df["is_weekend"] == 0)]

  if test_name in {"T02-evening_peak_hour", "T02"}:
    return df[(df["hour"] >= 16) & (df["hour"] <= 18) & (df["is_weekend"] == 0)]

  if test_name in {"T03-late_night_low_vol", "T03"}:
    return df[(df["hour"] >= 23) | (df["hour"] <= 2)]

  if test_name in {"T04-weekday_vs_weekend", "T04"}:
    return df[df["is_weekend"] == 1]

  if test_name in {"T05-mon_morning_vs_fri_afternoon", "T05"}:
    monday_morning = (df["day_of_week"] == 0) & (df["hour"] < 12)
    friday_afternoon = (df["day_of_week"] == 4) & (df["hour"] >= 12)
    return df[monday_morning | friday_afternoon]

  if test_name in {"T06-high_vol_intersection", "T06"}:
    avg_vol = df.groupby("scats_number")["actual"].mean()
    top_scats = avg_vol.idxmax()
    print(f"TC06: Highest volume intersection -> SCATS {top_scats} (avg {avg_vol[top_scats]:.2f})")
    return df[df["scats_number"] == top_scats]

  if test_name in {"T07-low_vol_intersection", "T07"}:
    avg_vol = df.groupby("scats_number")["actual"].mean()
    low_scats = avg_vol.idxmin()
    print(f"TC07: Lowest volume intersection -> SCATS {low_scats} (avg {avg_vol[low_scats]:.2f})")
    return df[df["scats_number"] == low_scats]

  if test_name in {"T08-full_mon", "T08"}:
    return df[df["day_of_week"] == 0]

  if test_name in {"T09-full_week", "T09"}:
    top_scats = df.groupby("scats_number").size().idxmax()
    print(f"TC09: Full week intersection -> SCATS {top_scats}")
    return df[df["scats_number"] == top_scats]

  if test_name in {"T10-transition_period", "T10"}:
    return df[(df["hour"] >= 6) & (df["hour"] <= 8)]

  print(f"Warning: No filter defined for '{test_name}', using full dataset.")
  return df


# Compute MAE, RMSE, and MAPE on the filtered subset.
def compute_metrics(actual, predicted):
  mae = float(np.mean(np.abs(actual - predicted)))
  rmse = float(np.sqrt(np.mean((actual - predicted) ** 2)))
  mask = actual != 0
  mape = float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100)
  return {"MAE": mae, "RMSE": rmse, "MAPE": mape}


# --------------------------------------
# --- Minh - Merge Existing Results  ---
# --------------------------------------

# Load any existing model metrics so new runs extend rather than overwrite them.
def load_existing_metrics(metrics_path: Path) -> dict:
  if not metrics_path.exists():
    return {}

  with open(metrics_path, "r", encoding="utf-8-sig") as f:
    try:
      return json.load(f)
    except json.JSONDecodeError:
      return {}


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--test", required=True, help="Test case name e.g. T01-morning_peak_hour")
  parser.add_argument(
    "--model",
    default="all",
    choices=AVAILABLE_MODELS + ["all"],
    help="Model to evaluate",
  )
  parser.add_argument("--data", default="2014", choices=["2006", "2014"], help="Predictions dataset to use")
  args = parser.parse_args()

  test_name = Path(args.test).stem
  predictions_path = PREDICTIONS_DIR / f"{args.data}_predictions.csv"

  if not predictions_path.exists():
    print(f"Error: '{predictions_path}' not found. Run predict.py --data {args.data} first.")
    return

  print(f"Loading predictions from {predictions_path}...")
  df = pd.read_csv(predictions_path, parse_dates=["datetime"], dayfirst=True)
  filtered = get_test_filter(test_name, df)

  if len(filtered) == 0:
    print(f"Error: No data found after applying filter for '{test_name}'.")
    return

  print(f"Test case '{test_name}': {len(filtered)} rows after filtering.")
  models_to_eval = AVAILABLE_MODELS if args.model == "all" else [args.model.lower()]

  RESULTS_DIR.mkdir(parents=True, exist_ok=True)
  GRAPH_DIR.mkdir(parents=True, exist_ok=True)
  all_metrics = {}

  for model_name in models_to_eval:
    pred_col = f"predicted_{model_name}"
    if pred_col not in filtered.columns:
      print(f"Error: Column '{pred_col}' not found in predictions CSV. Skipping.")
      continue

    actual = filtered["actual"].values
    predicted = filtered[pred_col].values
    metrics = compute_metrics(actual, predicted)
    all_metrics[model_name.upper()] = metrics

    print(f"\n{model_name.upper()} results on {test_name}:")
    print(f"  MAE  : {metrics['MAE']:.4f}")
    print(f"  RMSE : {metrics['RMSE']:.4f}")
    print(f"  MAPE : {metrics['MAPE']:.4f}%")

    plot_predictions(
      actual,
      predicted,
      title=f"{model_name.upper()} - {test_name}",
      output_dir=GRAPH_DIR,
      filename=f"{test_name}_{model_name}_predictions.png",
      show=False,
    )

  metrics_path = RESULTS_DIR / f"{test_name}_metrics.json"
  existing_metrics = load_existing_metrics(metrics_path)
  existing_metrics.update(all_metrics)
  with open(metrics_path, "w", encoding="utf-8") as f:
    json.dump(existing_metrics, f, indent=2)
  print(f"\nMetrics saved -> {metrics_path}")


if __name__ == "__main__":
  main()
