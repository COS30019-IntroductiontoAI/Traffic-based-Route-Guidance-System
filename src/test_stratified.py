"""
Test runner for evaluating models on the 20% stratified test split of 2006 dataset.
Generates predictions and runs all 10 test cases on only the data that was held out during training/validation.
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np

from src.data_loader import prepare_tabular_data
from src.evaluation import compute_metrics, plot_predictions
from src.test_filters import get_test_filter, get_test_cases
from src.config.model_config import SEQ_LEN, FORECAST_HORIZON

SRC_ROOT = Path(__file__).resolve().parent
PROCESSED_2006_PATH = SRC_ROOT / "data" / "processed" / "2006_processed.csv"
PREDICTIONS_DIR = SRC_ROOT / "results" / "predictions"
RESULTS_DIR = SRC_ROOT / "results" / "test_results"
GRAPH_DIR = SRC_ROOT / "results" / "test_graphs"
METRICS_CSV_PATH = RESULTS_DIR / "test_split_metrics.csv"
AVAILABLE_MODELS = ["lstm", "gru", "lightgbm"]


def extract_test_split_predictions():
    # Get the test split boundaries from the tabular data splitter
    _, _, _, _, test_df, train_end, val_end = prepare_tabular_data(
        filepath=str(PROCESSED_2006_PATH),
        seq_len=SEQ_LEN,
        forecast_horizon=FORECAST_HORIZON,
    )
    
    # Load the full 2006 predictions 
    full_predictions_path = PREDICTIONS_DIR / "2006_predictions.csv"
    if not full_predictions_path.exists():
        raise FileNotFoundError(
            f"Full predictions not found at {full_predictions_path}. "
            "Run: python -m src.predict --data 2006"
        )
    
    print(f"Loading full predictions from {full_predictions_path}...")
    full_predictions = pd.read_csv(full_predictions_path, parse_dates=["datetime"])
    
    # Ensure datetime column is properly converted to ISO8601 format
    full_predictions["datetime"] = pd.to_datetime(full_predictions["datetime"], format='ISO8601')
    
    # Filter to test split: only rows with datetime > val_end
    test_split_predictions = full_predictions[full_predictions["datetime"] > val_end].copy()
    
    print(f"Extracted {len(test_split_predictions)} rows for test split (from {len(full_predictions)} total)")
    print(f"Test split date range: {test_split_predictions['datetime'].min()} to {test_split_predictions['datetime'].max()}")
    
    return test_split_predictions


def save_test_split_predictions(test_predictions: pd.DataFrame) -> Path:
    output_path = PREDICTIONS_DIR / "2006_test_split_predictions.csv"
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    test_predictions.to_csv(output_path, index=False)
    print(f"Test split predictions saved -> {output_path}")
    return output_path


def run_stratified_tests(test_predictions: pd.DataFrame | None = None) -> dict:
    # Load predictions if not provided
    if test_predictions is None:
        test_predictions_path = PREDICTIONS_DIR / "2006_test_split_predictions.csv"
        if not test_predictions_path.exists():
            raise FileNotFoundError(
                f"Test split predictions not found at {test_predictions_path}. "
                "Run: generate_test_split_predictions() first"
            )
        print(f"Loading test split predictions from {test_predictions_path}...")
        test_predictions = pd.read_csv(test_predictions_path, parse_dates=["datetime"])
        
        # Ensure datetime column is properly converted to ISO8601 format
        test_predictions["datetime"] = pd.to_datetime(test_predictions["datetime"], format='ISO8601')
    
    print(f"\n{'='*80}")
    print(f"Running 10 Test Cases on 20% Test Split ({len(test_predictions)} rows)")
    print(f"{'='*80}")
    
    # Create result containers
    test_results = {}  # {test_id: {model: metrics}}
    csv_rows = []
    
    # Run each test case
    for test_case in get_test_cases():
        test_id = test_case["id"]
        test_name = test_case["name"]
        
        print(f"\n--- {test_id}: {test_case['description']} ---")
        
        # Apply test filter
        filtered_data = get_test_filter(test_id, test_predictions)
        n_samples = len(filtered_data)
        
        if n_samples == 0:
            print(f"  WARNING: No data matched filter for {test_id}")
            continue
        
        print(f"  Samples: {n_samples}")
        test_results[test_id] = {"n_samples": n_samples}
        
        # Evaluate each model
        for model_name in AVAILABLE_MODELS:
            pred_col = f"predicted_{model_name}"
            if pred_col not in filtered_data.columns:
                print(f"  WARNING: Column '{pred_col}' not found, skipping {model_name}")
                continue
            
            actual = filtered_data["actual"].values
            predicted = filtered_data[pred_col].values
            
            # Compute metrics using evaluation module
            metrics = compute_metrics(actual, predicted)
            test_results[test_id][model_name] = metrics
            
            print(f"  {model_name.upper():10s} | MAE: {metrics['MAE']:8.4f} | RMSE: {metrics['RMSE']:8.4f} | MAPE: {metrics['MAPE']:7.2f}%")
            
            # Record for CSV
            csv_rows.append({
                "test_id": test_id,
                "test_name": test_name,
                "model": model_name.upper(),
                "n_samples": n_samples,
                "mae": metrics["MAE"],
                "rmse": metrics["RMSE"],
                "mape": metrics["MAPE"],
            })
            
            # Generate comparison plot for test set
            test_graph_dir = GRAPH_DIR / test_id
            plot_predictions(
                actual,
                predicted,
                title=f"{model_name.upper()} - {test_id} (20% test split)",
                output_dir=test_graph_dir,
                filename=f"{model_name}_predictions.png",
                show=False,
            )
    
    # Save results to CSV
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    
    results_df = pd.DataFrame(csv_rows)
    results_df.to_csv(METRICS_CSV_PATH, index=False)
    print(f"\n✓ Test metrics saved -> {METRICS_CSV_PATH}")
    
    # Print summary table
    print(f"\n{'='*80}")
    print(f"SUMMARY: 10 Test Cases on 20% Test Split")
    print(f"{'='*80}")
    
    # Pivot for nice display
    for model in AVAILABLE_MODELS:
        print(f"\n{model.upper()} Model Results:")
        model_results = results_df[results_df["model"] == model.upper()].copy()
        model_results = model_results[["test_id", "n_samples", "mae", "rmse", "mape"]]
        print(model_results.to_string(index=False))
    
    return test_results


def main():
    try:
        # Generate test split predictions
        test_predictions = extract_test_split_predictions()
        save_test_split_predictions(test_predictions)
        
        # Run tests on the test split
        results = run_stratified_tests(test_predictions)
        
        print(f"\n{'='*80}")
        print("✓ Test stratification complete!")
        print(f"{'='*80}\n")
        
        return results
    except Exception as e:
        print(f"\n✗ Error during stratified testing: {e}")
        raise


if __name__ == "__main__":
    main()
