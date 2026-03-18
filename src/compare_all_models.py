from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.data_loader import prepare_data
from src.evaluation import evaluate_model

TRAINED_MODELS_DIR = PROJECT_ROOT / "results" / "trained_models"
METRICS_DIR = PROJECT_ROOT / "results" / "metrics"
GRAPHS_DIR = PROJECT_ROOT / "results" / "graphs"
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "processed_traffic.csv"
COMPARISON_PLOT_PATH = GRAPHS_DIR / "all_models_metrics_comparison.png"


# Save a metrics dictionary to a JSON file.
def save_metrics(metrics: dict, output_path: Path) -> None:
    output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")


# Evaluate one saved sequence model and store its metrics JSON.
def evaluate_sequence_metrics(model_name: str, model_filename: str) -> dict:
    (_, _), (x_val, y_val), (x_test, y_test), scaler = prepare_data(
        str(DATA_PATH),
        seq_len=96,
        forecast_horizon=1,
    )

    model_path = TRAINED_MODELS_DIR / model_filename
    _, _, val_metrics = evaluate_model(model_path, x_val, y_val, scaler)
    _, _, test_metrics = evaluate_model(model_path, x_test, y_test, scaler)

    metrics = {
        "validation": val_metrics,
        "test": test_metrics,
    }

    metrics_path = METRICS_DIR / f"{model_name}_metrics.json"
    save_metrics(metrics, metrics_path)
    return metrics


# Load the saved LightGBM metrics bundle from disk.
def load_lightgbm_metrics() -> dict:
    lightgbm_metrics_path = METRICS_DIR / "lightgbm_metrics.json"
    return json.loads(lightgbm_metrics_path.read_text(encoding="utf-8"))


# Plot MAE, RMSE, and MAPE for all three models in one grouped bar chart.
def plot_all_model_metrics(all_metrics: dict[str, dict]) -> None:
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

    metric_names = ["MAE", "RMSE", "MAPE"]
    model_names = list(all_metrics.keys())
    x = np.arange(len(metric_names))
    width = 0.25

    plt.figure(figsize=(10, 6))

    for index, model_name in enumerate(model_names):
        values = [all_metrics[model_name]["test"][metric] for metric in metric_names]
        plt.bar(x + (index - 1) * width, values, width=width, label=model_name)

    plt.xticks(x, metric_names)
    plt.ylabel("Metric Value")
    plt.title("MAE, RMSE, and MAPE Comparison Across Models")
    plt.legend()
    plt.tight_layout()
    plt.savefig(COMPARISON_PLOT_PATH)
    plt.close()


# Evaluate the sequence models, load LightGBM metrics, and create one comparison plot.
def main() -> None:
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

    print("Evaluating LSTM model...")
    lstm_metrics = evaluate_sequence_metrics("lstm", "lstm_model.keras")

    print("Evaluating GRU model...")
    gru_metrics = evaluate_sequence_metrics("gru", "gru_model.keras")

    print("Loading LightGBM metrics...")
    lightgbm_metrics = load_lightgbm_metrics()

    all_metrics = {
        "LSTM": lstm_metrics,
        "GRU": gru_metrics,
        "LightGBM": lightgbm_metrics,
    }

    plot_all_model_metrics(all_metrics)

    print("LSTM metrics:", lstm_metrics)
    print("GRU metrics:", gru_metrics)
    print("LightGBM metrics:", lightgbm_metrics)
    print("Comparison plot saved to:", COMPARISON_PLOT_PATH.name)


if __name__ == "__main__":
    main()
