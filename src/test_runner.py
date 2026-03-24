import argparse
import numpy as np
import pandas as pd
import json
from pathlib import Path
from src.evaluation import plot_predictions

PREDICTIONS_DIR = Path("results/predictions")
RESULTS_DIR = Path("results/test_results")
GRAPH_DIR = Path("results/test_graphs")


# Returns a filtered dataframe based on the test case name
# Each test case targets a specific traffic scenario using column-level filters
def get_test_filter(test_name, df):

  # TC01: Weekday morning peak hours (7:00 AM - 9:45 AM)
  if test_name == "T01-morning_peak_hour" or test_name == "T01":
    return df[(df["hour"] >= 7) & (df["hour"] <= 9) & (df["is_weekend"] == 0)]

  # TC02: Weekday evening peak hours (4:00 PM - 6:45 PM)
  if test_name == "T02-evening_peak_hour" or test_name == "T02":
    return df[(df["hour"] >= 16) & (df["hour"] <= 18) & (df["is_weekend"] == 0)]

  # TC03: Late night low volume period (11:00 PM - 2:45 AM)
  if test_name == "T03-late_night_low_vol" or test_name == "T03":
    return df[(df["hour"] >= 23) | (df["hour"] <= 2)]

  # TC04: Weekend traffic (contrasts weekday peak behavior in TC01/TC02)
  if test_name == "T04-weekday_vs_weekend" or test_name == "T04":
    return df[df["is_weekend"] == 1]

  # TC05: Monday morning vs Friday afternoon (start vs end of week patterns)
  if test_name == "T05-mon_morning_vs_fri_afternoon" or test_name == "T05":
    monday_morning = (df["day_of_week"] == 0) & (df["hour"] < 12)
    friday_afternoon = (df["day_of_week"] == 4) & (df["hour"] >= 12)
    return df[monday_morning | friday_afternoon]

  # TC06: Highest average volume intersection (stress test for heavy load)
  if test_name == "T06-high_vol_intersection" or test_name == "T06":
    avg_vol = df.groupby("scats_number")["actual"].mean()
    top_scats = avg_vol.idxmax()
    print(f"TC06: Highest volume intersection → SCATS {top_scats} (avg {avg_vol[top_scats]:.2f})")
    return df[df["scats_number"] == top_scats]

  # TC07: Lowest average volume intersection (quiet residential roads)
  if test_name == "T07-low_vol_intersection" or test_name == "T07":
    avg_vol = df.groupby("scats_number")["actual"].mean()
    low_scats = avg_vol.idxmin()
    print(f"TC07: Lowest volume intersection → SCATS {low_scats} (avg {avg_vol[low_scats]:.2f})")
    return df[df["scats_number"] == low_scats]

  # TC08: All intervals on Mondays (full day temporal consistency check)
  if test_name == "T08-full_mon" or test_name == "T08":
    return df[df["day_of_week"] == 0]

  # TC09: Full week for the intersection with the most data (cross-day stability)
  if test_name == "T09-full_week" or test_name == "T09":
    top_scats = df.groupby("scats_number").size().idxmax()
    print(f"TC09: Full week intersection → SCATS {top_scats}")
    return df[df["scats_number"] == top_scats]

  # TC10: Morning transition period (6:00 AM - 8:45 AM, ramp-up from low to peak)
  if test_name == "T10-transition_period" or test_name == "T10":
    return df[(df["hour"] >= 6) & (df["hour"] <= 8)]

  print(f"Warning: No filter defined for '{test_name}', using full dataset.")
  return df


# Compute evaluation metrics: MAE, RMSE, MAPE (zero-masked)
def compute_metrics(actual, predicted):
  mae  = float(np.mean(np.abs(actual - predicted)))
  rmse = float(np.sqrt(np.mean((actual - predicted) ** 2)))

  # Filter out zero values before computing MAPE to avoid division by zero
  mask = actual != 0
  mape = float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100)

  return {"MAE": mae, "RMSE": rmse, "MAPE": mape}


def main():
  # Parse command line arguments
  parser = argparse.ArgumentParser()
  parser.add_argument("--test",  required=True, help="Test case name e.g. T01-morning_peak_hour")
  parser.add_argument("--model", default="all", choices=["lstm", "gru", "all"], help="Model to evaluate")
  parser.add_argument("--data",  default="2014", choices=["2006", "2014"], help="Predictions dataset to use")
  args = parser.parse_args()

  test_name = Path(args.test).stem



  # -------------------------------
  # --- 1. LOAD PREDICTIONS CSV ---
  # -------------------------------
  predictions_path = PREDICTIONS_DIR / f"{args.data}_predictions.csv"

  if not predictions_path.exists():
    print(f"Error: '{predictions_path}' not found. Run predict.py --data {args.data} first.")
    return

  print(f"Loading predictions from {predictions_path}...")
  df = pd.read_csv(predictions_path, parse_dates=["datetime"])



  # ---------------------------------
  # --- 2. APPLY TEST CASE FILTER ---
  # ---------------------------------
  filtered = get_test_filter(test_name, df)

  if len(filtered) == 0:
    print(f"Error: No data found after applying filter for '{test_name}'.")
    return

  print(f"Test case '{test_name}': {len(filtered)} rows after filtering.")



  # ---------------------------------------------
  # --- 3. DETERMINE WHICH MODELS TO EVALUATE ---
  # ---------------------------------------------
  models_to_eval = ["lstm", "gru"] if args.model == "all" else [args.model.lower()]



  # --------------------------------------------------
  # --- 4. COMPUTE METRICS AND PLOT FOR EACH MODEL ---
  # --------------------------------------------------
  RESULTS_DIR.mkdir(parents=True, exist_ok=True)
  GRAPH_DIR.mkdir(parents=True, exist_ok=True)
  all_metrics = {}

  for model_name in models_to_eval:
    pred_col = f"predicted_{model_name}"

    if pred_col not in filtered.columns:
      print(f"Error: Column '{pred_col}' not found in predictions CSV. Skipping.")
      continue

    actual    = filtered["actual"].values
    predicted = filtered[pred_col].values

    # Compute metrics on the filtered subset
    metrics = compute_metrics(actual, predicted)
    all_metrics[model_name.upper()] = metrics

    print(f"\n{model_name.upper()} results on {test_name}:")
    print(f"  MAE  : {metrics['MAE']:.4f}")
    print(f"  RMSE : {metrics['RMSE']:.4f}")
    print(f"  MAPE : {metrics['MAPE']:.4f}%")

    # Plot actual vs predicted values for visual comparison
    plot_predictions(
      actual, predicted,
      title=f"{model_name.upper()} — {test_name}",
      output_dir=GRAPH_DIR,
      filename=f"{test_name}_{model_name}_predictions.png",
      show=False
    )



  # -----------------------------------------
  # --- 5. SAVE TEST RESULTS TO JSON FILE ---
  # -----------------------------------------
  metrics_path = RESULTS_DIR / f"{test_name}_metrics.json"
  with open(metrics_path, "w") as f:
    json.dump(all_metrics, f, indent=2)
  print(f"\nMetrics saved → {metrics_path}")


if __name__ == "__main__":
  main()