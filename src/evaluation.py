import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error
from lightgbm import Booster
from tensorflow.keras.models import load_model

from src.data_loader import prepare_data, prepare_tabular_data
from src.config.model_config import SEQ_LEN, FORECAST_HORIZON
from src.predict import MODEL_SPECS, predict_tabular_model


SRC_ROOT = Path(__file__).resolve().parent
GRAPH_DIR = SRC_ROOT / "results" / "graphs"
METRICS_DIR = SRC_ROOT / "results" / "metrics"
PROCESSED_2006_PATH = SRC_ROOT / "data" / "processed" / "2006_processed.csv"


# Inverse transform the data using the scaler
def inverse_transform(scaler, data):
  flat = data.flatten()
  dummy = np.zeros((len(flat), scaler.n_features_in_))
  dummy[:, 0] = flat
  inversed = scaler.inverse_transform(dummy)[:, 0]
  
  # Undo the log1p transform
  return np.expm1(inversed)


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


# Evaluate one saved sequence model on one split.
def evaluate_sequence_model(model_path, X_test, y_test, scaler):
  # Load the saved model and make predictions on the test set
  model = load_model(model_path) 
  predictions = model.predict(X_test)
  
  # Inverse transform the predictions and actual values to get them back to the original scale
  actual_real = inverse_transform(scaler, y_test)
  predicted_real = inverse_transform(scaler, predictions.flatten())
  
  # Compute the evaluation metrics
  metrics = compute_metrics(actual_real, predicted_real)
  
  return actual_real, predicted_real, metrics


# Backward-compatible alias for older imports.
def evaluate_model(model_path, X_test, y_test, scaler):
  return evaluate_sequence_model(model_path, X_test, y_test, scaler)


# Plot the actual vs predicted values for visual comparison
def plot_predictions(actual, predicted, title, output_dir: Path = GRAPH_DIR, filename: str = None, show: bool = False):
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

  if show:
    plt.show()

  plt.close()
  return save_path

# Compute metrics when predictions are already available for tabular models.
def evaluate_tabular_predictions(actual: np.ndarray, predicted: np.ndarray) -> dict:
  return compute_metrics(actual, predicted)


# Evaluate one tabular model on one prepared dataframe split.
def evaluate_tabular_model(model, split_df, feature_columns: list[str], target_column: str = "traffic_volume"):
  actual = split_df[target_column].to_numpy(dtype=float)
  predicted = predict_tabular_model(model, split_df, feature_columns)
  metrics = evaluate_tabular_predictions(actual, predicted)
  return actual, predicted, metrics


# Build the shared validation/test contexts used by different model kinds.
def build_evaluation_context():
  (_, _), (X_val, y_val), (X_test, y_test), scaler, label_encoder = prepare_data(
    filepath=str(PROCESSED_2006_PATH),
    seq_len=SEQ_LEN,
    forecast_horizon=FORECAST_HORIZON
  )
  _, feature_columns, _, val_df, test_df, train_end, val_end = prepare_tabular_data(
    filepath=str(PROCESSED_2006_PATH),
    seq_len=SEQ_LEN,
    forecast_horizon=FORECAST_HORIZON,
  )
  return {
    "sequence": {
      "validation": (X_val, y_val),
      "test": (X_test, y_test),
      "scaler": scaler,
    },
    "tabular": {
      "validation": val_df,
      "test": test_df,
      "feature_columns": feature_columns,
      "train_end": train_end,
      "val_end": val_end,
    },
  }


# Evaluate one model spec on validation and test and return a shared metrics bundle.
def evaluate_model_spec(spec: dict, context: dict, graph_dir: Path) -> dict:
  metrics_bundle = {}

  if spec["kind"] == "sequence":
    scaler = context["sequence"]["scaler"]
    for split_name, (X_split, y_split) in {
      "validation": context["sequence"]["validation"],
      "test": context["sequence"]["test"],
    }.items():
      actual, predicted, split_metrics = evaluate_sequence_model(spec["path"], X_split, y_split, scaler)
      metrics_bundle[split_name] = split_metrics

      if split_name == "test":
        plot_path = plot_predictions(
          actual,
          predicted,
          title=f"{spec['name'].upper()} Predictions ({split_name})",
          output_dir=graph_dir,
          filename=f"{spec['name']}_{split_name}_predictions.png",
          show=False,
        )
        print(f"{split_name.capitalize()} plot -> {plot_path}")

      print(f"{spec['name'].upper()} {split_name} MAE  : {split_metrics['MAE']:.4f}")
      print(f"{spec['name'].upper()} {split_name} RMSE : {split_metrics['RMSE']:.4f}")
      print(f"{spec['name'].upper()} {split_name} MAPE : {split_metrics['MAPE']:.4f}%")

    return metrics_bundle

  if spec["kind"] == "tabular":
    model = Booster(model_file=str(spec["path"]))
    feature_columns = context["tabular"]["feature_columns"]
    for split_name, split_df in {
      "validation": context["tabular"]["validation"],
      "test": context["tabular"]["test"],
    }.items():
      actual, predicted, split_metrics = evaluate_tabular_model(model, split_df, feature_columns)
      metrics_bundle[split_name] = split_metrics

      if split_name == "test":
        plot_path = plot_predictions(
          actual,
          predicted,
          title=f"{spec['name'].upper()} Predictions ({split_name})",
          output_dir=graph_dir,
          filename=f"{spec['name']}_{split_name}_predictions.png",
          show=False,
        )
        print(f"{split_name.capitalize()} plot -> {plot_path}")

      print(f"{spec['name'].upper()} {split_name} MAE  : {split_metrics['MAE']:.4f}")
      print(f"{spec['name'].upper()} {split_name} RMSE : {split_metrics['RMSE']:.4f}")
      print(f"{spec['name'].upper()} {split_name} MAPE : {split_metrics['MAPE']:.4f}%")

    return metrics_bundle

  return metrics_bundle
  

# Save the evaluation metrics to a JSON file for easy reference and comparison
def save_metrics_json(model_name: str, metrics: dict, output_dir: Path = METRICS_DIR) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  metrics_path = output_dir / f"{model_name.lower()}_metrics.json"
  with metrics_path.open("w", encoding="utf-8") as fp:
    json.dump(metrics, fp, indent=2)
  return metrics_path


# Main function to evaluate all saved models and generate metrics and plots
def evaluate_saved_models(graph_dir: Path = GRAPH_DIR, metrics_dir: Path = METRICS_DIR):
  print("Loading validation and test data...")
  context = build_evaluation_context()
  X_val, y_val = context["sequence"]["validation"]
  X_test, y_test = context["sequence"]["test"]
  print(f"X_val shape : {X_val.shape}")
  print(f"y_val shape : {y_val.shape}")
  print(f"X_test shape: {X_test.shape}")
  print(f"y_test shape: {y_test.shape}")
  print(f"LightGBM train_end: {context['tabular']['train_end']}")
  print(f"LightGBM val_end  : {context['tabular']['val_end']}")

  for spec in MODEL_SPECS:
    if not spec["path"].exists():
      print(f"\nSkipping {spec['name'].upper()} evaluation because the model artifact is missing.")
      continue

    print(f"\nEvaluating {spec['name'].upper()} model...")
    metrics_bundle = evaluate_model_spec(spec, context, graph_dir)
    metrics_path = save_metrics_json(spec["name"].upper(), metrics_bundle, output_dir=metrics_dir)
    print(f"Saved metrics -> {metrics_path}")

  print("\nDone!")


if __name__ == "__main__":
  evaluate_saved_models()
