import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error
from tensorflow.keras.models import load_model

from src.data_loader import prepare_data
from src.model_config import SEQ_LEN, FORECAST_HORIZON


GRAPH_DIR = Path("results/graphs")
METRICS_DIR = Path("results/metrics")


# Inverse transform the data using the scaler
def inverse_transform(scaler, data: np.ndarray) -> np.ndarray:
  flat = data.flatten()

  dummy = np.zeros((len(flat), scaler.n_features_in_))
  dummy[:, 0] = flat   

  inversed = scaler.inverse_transform(dummy)

  return inversed[:, 0]


# Compute evaluation metrics: MAE, RMSE, and MAPE
def compute_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
  mae = mean_absolute_error(actual, predicted)
  rmse = np.sqrt(mean_squared_error(actual, predicted))
  
  # Filter out zero values before computing MAPE
  mask = actual != 0         
  actual_masked = actual[mask]
  predicted_masked = predicted[mask]
  
  mape = np.mean(np.abs((actual_masked - predicted_masked) / actual_masked)) * 100
  
  return { "MAE": float(mae), "RMSE": float(rmse), "MAPE": float(mape) }


# Main function to evaluate the model on the test set
def evaluate_model(model_path, X_test, y_test, scaler):
  # Load the saved model and make predictions on the test set
  model = load_model(model_path) 
  predictions = model.predict(X_test)
  
  # Inverse transform the predictions and actual values to get them back to the original scale
  actual_real = inverse_transform(scaler, y_test)
  predicted_real = inverse_transform(scaler, predictions.flatten())
  
  # Compute the evaluation metrics
  metrics = compute_metrics(actual_real, predicted_real)
  
  return actual_real, predicted_real, metrics


# Plot the actual vs predicted values for visual comparison
def plot_predictions(actual, predicted, title, output_dir: Path = GRAPH_DIR, filename: str = None, show: bool = False):
  output_dir.mkdir(parents=True, exist_ok=True)
  save_name = filename or f"{title.lower().replace(' ', '_')}.png"
  save_path = output_dir / save_name

  plt.figure(figsize=(14, 5))
  plt.plot(actual, label="Actual", color="blue")
  plt.plot(predicted, label="Predicted", color="orange")
  plt.title(title)
  plt.xlabel("Time Steps")
  plt.ylabel("Traffic Volume")
  plt.legend()
  plt.savefig(save_path, bbox_inches="tight")

  if show:
    plt.show()

  plt.close()
  return save_path
  

def save_metrics_json(model_name: str, metrics: dict, output_dir: Path = METRICS_DIR) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  metrics_path = output_dir / f"{model_name.lower()}_metrics.json"
  with metrics_path.open("w", encoding="utf-8") as fp:
    json.dump(metrics, fp, indent=2)
  return metrics_path


def evaluate_saved_models(graph_dir: Path = GRAPH_DIR, metrics_dir: Path = METRICS_DIR):
  print("Loading validation and test data...")
  (_, _), (X_val, y_val), (X_test, y_test), scaler = prepare_data(
    filepath="data/processed/processed_traffic.csv",
    seq_len=SEQ_LEN,
    forecast_horizon=FORECAST_HORIZON
  )
  print(f"X_val shape : {X_val.shape}")
  print(f"y_val shape : {y_val.shape}")
  print(f"X_test shape: {X_test.shape}")
  print(f"y_test shape: {y_test.shape}")

  models = [
    ("LSTM", "results/trained_models/lstm_model.keras"),
    ("GRU", "results/trained_models/gru_model.keras"),
  ]

  for model_name, model_path in models:
    print(f"\nEvaluating {model_name} model...")
    metrics_bundle = {}

    for split_name, (X_split, y_split) in {
      "validation": (X_val, y_val),
      "test": (X_test, y_test),
    }.items():
      actual, predicted, split_metrics = evaluate_model(model_path, X_split, y_split, scaler)
      metrics_bundle[split_name] = split_metrics

      # Only plot test predictions to keep artifacts light
      if split_name == "test":
        plot_path = plot_predictions(
          actual,
          predicted,
          title=f"{model_name} Predictions ({split_name})",
          output_dir=graph_dir,
          filename=f"{model_name.lower()}_{split_name}_predictions.png",
          show=False,
        )
        print(f"{split_name.capitalize()} plot -> {plot_path}")

      print(f"{model_name} {split_name} MAE  : {split_metrics['MAE']:.4f}")
      print(f"{model_name} {split_name} RMSE : {split_metrics['RMSE']:.4f}")
      print(f"{model_name} {split_name} MAPE : {split_metrics['MAPE']:.4f}%")

    metrics_path = save_metrics_json(model_name, metrics_bundle, output_dir=metrics_dir)
    print(f"Saved metrics -> {metrics_path}")

  print("\nDone!")


if __name__ == "__main__":
  evaluate_saved_models()
