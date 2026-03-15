from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.predict import predict_sequence_model

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
GRAPHS_DIR = PROJECT_ROOT / "results" / "graphs"


# ------------------------------
# --- Common Metric Helpers ---
# ------------------------------

# Compute evaluation metrics: MAE, RMSE, and MAPE
def compute_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
  mae = float(mean_absolute_error(actual, predicted))
  rmse = float(np.sqrt(mean_squared_error(actual, predicted)))

  non_zero_mask = actual != 0
  if np.any(non_zero_mask):
    mape = float(np.mean(np.abs((actual[non_zero_mask] - predicted[non_zero_mask]) / actual[non_zero_mask])) * 100)
  else:
    mape = 0.0
  
  return { "MAE": mae, "RMSE": rmse, "MAPE": mape }


# ----------------------------------------
# --- Sequence-Based Evaluation Helper ---
# ----------------------------------------

# Main function to evaluate the model on the test set
def evaluate_model(model_path, X_testt, y_test, scaler):
  # Load the saved model and make predictions on the test set
  actual_real, predicted_real = predict_sequence_model(model_path, X_testt, y_test, scaler)
  
  # Compute the evaluation metrics and print them
  metrics = compute_metrics(actual_real, predicted_real)
  print(f"Evaluation Metrics for {model_path}:")
  
  return actual_real, predicted_real, metrics


# Plot the actual vs predicted values for visual comparison
def plot_predictions(actual, predicted, title, output_path: str | Path | None = None):
  GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
  plt.figure(figsize=(14, 5))
  plt.plot(actual, label="Actual", color="blue")
  plt.plot(predicted, label="Predicted", color="orange")
  plt.title(title)
  plt.xlabel("Time Steps")
  plt.ylabel("Traffic Volume")
  plt.legend()

  if output_path is None:
    output_path = GRAPHS_DIR / f"{title.lower().replace(' ', '_')}_predictions.png"

  plt.savefig(output_path)
  plt.close()
  

# Compare the evaluation metrics of LSTM and GRU models using bar charts
def compare_metrics(lstm_metrics, gru_metrics):
  GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
  metrics_names = ["MAE", "RMSE", "MAPE"]
  
  for metric in metrics_names:
    plt.bar(["LSTM", "GRU"], [lstm_metrics[metric], gru_metrics[metric]], color=["blue", "orange"])
    plt.title(f"Comparison of {metric} between LSTM and GRU")
    plt.ylabel(metric)
    plt.savefig(GRAPHS_DIR / f"comparison_{metric.lower()}.png")
    plt.close()


# --------------------------------
# --- XGBoost Evaluation Helper ---
# --------------------------------

# Compute metrics when predictions are already available.
def evaluate_tabular_predictions(actual: np.ndarray, predicted: np.ndarray) -> dict:
  return compute_metrics(actual, predicted)
