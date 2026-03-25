from __future__ import annotations

import json
from pathlib import Path

from lightgbm import LGBMRegressor, early_stopping

from src.data_loader import prepare_tabular_data
from src.evaluation import evaluate_tabular_predictions, plot_predictions
from src.predict import predict_tabular_model

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TRAINED_MODELS_DIR = PROJECT_ROOT / "results" / "trained_models"
METRICS_DIR = PROJECT_ROOT / "results" / "metrics"
GRAPHS_DIR = PROJECT_ROOT / "results" / "graphs"
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "2006_processed.csv"
MODEL_PATH = TRAINED_MODELS_DIR / "lightgbm_model.txt"
METADATA_PATH = TRAINED_MODELS_DIR / "lightgbm_metadata.json"
METRICS_PATH = METRICS_DIR / "lightgbm_metrics.json"

TARGET_COLUMN = "traffic_volume"
SEQUENCE_LENGTH = 96
FORECAST_HORIZON = 1


# Return feature matrix X and target vector y from a prepared dataframe.
def get_xy(df, feature_columns: list[str]):
  return df[feature_columns], df[TARGET_COLUMN]


# Build the shared LightGBM regressor for the tabular pipeline.
def create_model() -> LGBMRegressor:
  return LGBMRegressor(
    objective="poisson",
    device="cpu",
    n_estimators=2200,
    learning_rate=0.03,
    num_leaves=255,
    max_depth=12,
    min_child_samples=80,
    subsample=1.0,
    colsample_bytree=0.6,
    reg_alpha=0.05,
    reg_lambda=1.0,
    random_state=42,
    verbose=-1,
  )


# Save the split settings and feature layout used for inference later.
def save_metadata(train_end, val_end, row_count: int, feature_columns: list[str]) -> None:
  TRAINED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
  metadata = {
    "data_path": str(DATA_PATH),
    "feature_columns": feature_columns,
    "target_column": TARGET_COLUMN,
    "sequence_length": SEQUENCE_LENGTH,
    "forecast_horizon": FORECAST_HORIZON,
    "train_end": train_end.isoformat(),
    "val_end": val_end.isoformat(),
    "row_count_after_features": row_count,
    "categorical_features": ["scats_number", "location"],
  }
  METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


# Build the movement-level tabular splits from the shared data loader.
def prepare_datasets():
  return prepare_tabular_data(str(DATA_PATH), SEQUENCE_LENGTH, FORECAST_HORIZON)


# Select one representative movement slice so the saved plot stays readable.
def build_plot_slice(test_df, predictions, max_points: int = 400):
  plot_df = test_df[["movement_id", "datetime", TARGET_COLUMN]].copy()
  plot_df["predicted"] = predictions

  representative_movement = plot_df["movement_id"].value_counts().idxmax()
  movement_plot_df = (
    plot_df[plot_df["movement_id"] == representative_movement]
    .sort_values("datetime")
    .head(max_points)
  )

  title = f"LightGBM Predictions - {representative_movement}"
  actual = movement_plot_df[TARGET_COLUMN].to_numpy(dtype=float)
  predicted = movement_plot_df["predicted"].to_numpy(dtype=float)
  return actual, predicted, title


# Train the LightGBM model and save model, metadata, metrics, and graph.
def train_lightgbm_model() -> tuple[LGBMRegressor, dict[str, dict[str, float]]]:
  TRAINED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
  METRICS_DIR.mkdir(parents=True, exist_ok=True)
  GRAPHS_DIR.mkdir(parents=True, exist_ok=True)

  feature_df, feature_columns, train_df, val_df, test_df, train_end, val_end = prepare_datasets()
  x_train, y_train = get_xy(train_df, feature_columns)
  x_val, y_val = get_xy(val_df, feature_columns)
  x_test, y_test = get_xy(test_df, feature_columns)

  model = create_model()
  model.fit(
    x_train,
    y_train,
    eval_set=[(x_val, y_val)],
    eval_metric="rmse",
    callbacks=[early_stopping(80, verbose=False)],
  )

  val_predictions = predict_tabular_model(model, val_df, feature_columns)
  test_predictions = predict_tabular_model(model, test_df, feature_columns)
  val_metrics = evaluate_tabular_predictions(y_val.to_numpy(dtype=float), val_predictions)
  test_metrics = evaluate_tabular_predictions(y_test.to_numpy(dtype=float), test_predictions)

  model.booster_.save_model(str(MODEL_PATH))
  save_metadata(train_end, val_end, len(feature_df), feature_columns)
  METRICS_PATH.write_text(
    json.dumps({"validation": val_metrics, "test": test_metrics}, indent=2),
    encoding="utf-8",
  )

  plot_actual, plot_predicted, plot_title = build_plot_slice(test_df, test_predictions)
  plot_predictions(
    plot_actual,
    plot_predicted,
    plot_title,
    output_dir=GRAPHS_DIR,
    filename="lightgbm_predictions.png",
    show=False,
  )

  return model, {"validation": val_metrics, "test": test_metrics}


# Run end-to-end training from the command line.
def main() -> None:
  print("Training LightGBM model...")
  _, metrics = train_lightgbm_model()
  print("Training completed.")
  print("Validation metrics:", metrics["validation"])
  print("Test metrics:", metrics["test"])


if __name__ == "__main__":
  main()
