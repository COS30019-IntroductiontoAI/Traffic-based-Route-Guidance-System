import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import Booster
from tensorflow.keras.models import load_model

from src.config.model_config import FORECAST_HORIZON, SEQ_LEN
from src.data_loader import (
  SEQUENCE_FEATURE_COLUMNS,
  add_common_time_features,
  create_sequences,
  create_tabular_sequences_by_movement,
  encode_road_names,
  load_movement_level_data,
  prepare_data,
  read_processed_data,
)

SRC_ROOT = Path(__file__).resolve().parent
PROCESSED_DIR = SRC_ROOT / "data" / "processed"
PREDICTIONS_DIR = SRC_ROOT / "results" / "predictions"
MODEL_DIR = SRC_ROOT / "results" / "trained_models"
LIGHTGBM_MODEL_PATH = MODEL_DIR / "lightgbm_model.txt"
LIGHTGBM_METADATA_PATH = MODEL_DIR / "lightgbm_metadata.json"

MODEL_SPECS = [
  {"name": "lstm", "kind": "sequence", "path": MODEL_DIR / "lstm_model.keras"},
  {"name": "gru", "kind": "sequence", "path": MODEL_DIR / "gru_model.keras"},
  {
    "name": "lightgbm",
    "kind": "tabular",
    "path": LIGHTGBM_MODEL_PATH,
    "metadata_path": LIGHTGBM_METADATA_PATH,
  },
]


# Run inference for a tabular model on prepared feature columns.
def predict_tabular_model(model, feature_df: pd.DataFrame, feature_columns: list[str]) -> np.ndarray:
  return model.predict(feature_df[feature_columns])


# Inverse-transform the sequence target back to raw traffic volume.
def inverse_scale_y(scaler, scaled_arr):
  dummy = np.zeros((len(scaled_arr), scaler.n_features_in_))
  dummy[:, 0] = scaled_arr
  return np.expm1(scaler.inverse_transform(dummy)[:, 0])


# Build the shared sequence prediction context once for all sequence models.
def build_sequence_context(filepath: Path, scaler, label_encoder) -> tuple[pd.DataFrame, np.ndarray]:
  df = read_processed_data(str(filepath))
  df = add_common_time_features(df)
  df["traffic_volume"] = np.log1p(df["traffic_volume"])
  df, _ = encode_road_names(df, label_encoder)

  X_all, y_all, meta_all = [], [], []
  for (_, _), group in df.groupby(["scats_number", "location"]):
    if len(group) < SEQ_LEN + FORECAST_HORIZON:
      continue

    features = group[SEQUENCE_FEATURE_COLUMNS].values
    X_seq, y_seq = create_sequences(features, SEQ_LEN, FORECAST_HORIZON)
    if len(X_seq) == 0:
      continue

    meta = group.iloc[SEQ_LEN: SEQ_LEN + len(X_seq)][
      ["datetime", "scats_number", "location", "hour", "day_of_week", "is_weekend"]
    ].reset_index(drop=True)
    X_all.append(X_seq)
    y_all.append(y_seq)
    meta_all.append(meta)

  if len(X_all) == 0:
    raise ValueError("No valid sequences found. Check dataset.")

  X = np.concatenate(X_all)
  y = np.concatenate(y_all)
  meta_df = pd.concat(meta_all, ignore_index=True)

  shape = X.shape
  X_scaled = scaler.transform(X.reshape(-1, shape[-1])).reshape(shape)
  y_scaled = scaler.transform(
    np.column_stack([y, np.zeros((len(y), scaler.n_features_in_ - 1))])
  )[:, 0]

  results_df = meta_df.copy()
  results_df["actual"] = inverse_scale_y(scaler, y_scaled)
  return results_df, X_scaled


# Run one model spec and return its prediction series keyed by datetime/site/location.
def build_model_predictions(spec: dict, filepath: Path, scaler, label_encoder, sequence_results: pd.DataFrame, X_scaled):
  if not spec["path"].exists():
    print(f"Warning: {spec['path']} not found, skipping {spec['name'].upper()}.")
    return None

  model_name = spec["name"]
  print(f"Predicting with {model_name.upper()}...")

  if spec["kind"] == "sequence":
    model = load_model(spec["path"])
    y_pred_scaled = model.predict(X_scaled, verbose=0)
    predictions_df = sequence_results[["datetime", "scats_number", "location"]].copy()
    predictions_df[f"predicted_{model_name}"] = inverse_scale_y(scaler, y_pred_scaled.flatten())
    print(f"{model_name.upper()} done.")
    return predictions_df

  if spec["kind"] == "tabular":
    metadata = json.loads(spec["metadata_path"].read_text(encoding="utf-8-sig"))
    movement_df = load_movement_level_data(str(filepath))
    feature_df = create_tabular_sequences_by_movement(
      movement_df,
      int(metadata["sequence_length"]),
      int(metadata["forecast_horizon"]),
    )
    model = Booster(model_str=spec["path"].read_text(encoding="utf-8-sig"))
    predictions_df = feature_df[["datetime", "scats_number", "location"]].copy()
    predictions_df[f"predicted_{model_name}"] = predict_tabular_model(
      model,
      feature_df,
      metadata["feature_columns"],
    )
    print(f"{model_name.upper()} done.")
    return predictions_df

  return None


# Build one merged prediction table that contains all available model outputs.
def build_predictions_table(filepath: Path, scaler, label_encoder) -> pd.DataFrame:
  results_df, X_scaled = build_sequence_context(filepath, scaler, label_encoder)
  results_df["datetime"] = pd.to_datetime(results_df["datetime"])

  for spec in MODEL_SPECS:
    predictions_df = build_model_predictions(spec, filepath, scaler, label_encoder, results_df, X_scaled)
    if predictions_df is None:
      continue

    predictions_df["datetime"] = pd.to_datetime(predictions_df["datetime"])
    results_df = results_df.merge(
      predictions_df,
      on=["datetime", "scats_number", "location"],
      how="left",
    )

  return results_df


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--data", required=True, choices=["2006", "2014"], help="Dataset to predict on")
  args = parser.parse_args()

  print("Loading 2006 scaler and label encoder...")
  (_, _), (_, _), (_, _), scaler, label_encoder = prepare_data(
    filepath=str(PROCESSED_DIR / "2006_processed.csv"),
    seq_len=SEQ_LEN,
    forecast_horizon=FORECAST_HORIZON,
  )

  filepath = PROCESSED_DIR / f"{args.data}_processed.csv"
  if not filepath.exists():
    print(f"Error: Dataset file '{filepath}' not found.")
    return

  print(f"Loading {filepath}...")
  try:
    results_df = build_predictions_table(filepath, scaler, label_encoder)
  except ValueError as exc:
    print(f"Error: {exc}")
    return

  PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
  output_path = PREDICTIONS_DIR / f"{args.data}_predictions.csv"
  results_df.to_csv(output_path, index=False)
  print(f"\nPredictions saved -> {output_path}")


if __name__ == "__main__":
  main()
