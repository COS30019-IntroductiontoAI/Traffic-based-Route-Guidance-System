"""Batch prediction entrypoint for sequence and tabular model artifacts.

This module performs inference only. It does not train any model and explicitly
loads pre-trained sequence artifacts from results/trained_models.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from lightgbm import Booster
import tensorflow as tf

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
from src.models.model_loader import load_sequence_model_artifacts

LOGGER = logging.getLogger(__name__)

SRC_ROOT: Path = Path(__file__).resolve().parent
PROCESSED_DIR: Path = SRC_ROOT / "data" / "processed"
PREDICTIONS_DIR: Path = SRC_ROOT / "results" / "predictions"
MODEL_DIR: Path = SRC_ROOT / "results" / "trained_models"
LIGHTGBM_MODEL_PATH: Path = MODEL_DIR / "lightgbm_model.txt"
LIGHTGBM_METADATA_PATH: Path = MODEL_DIR / "lightgbm_metadata.json"

MODEL_SPECS: list[dict[str, Any]] = [
  {"name": "lstm", "kind": "sequence", "path": MODEL_DIR / "lstm_model.keras"},
  {"name": "gru", "kind": "sequence", "path": MODEL_DIR / "gru_model.keras"},
  {
    "name": "lightgbm",
    "kind": "tabular",
    "path": LIGHTGBM_MODEL_PATH,
    "metadata_path": LIGHTGBM_METADATA_PATH,
  },
]


def predict_tabular_model(model: Booster, feature_df: pd.DataFrame, feature_columns: list[str]) -> np.ndarray:
  """Run inference for a tabular model on selected feature columns.

  Args:
    model: Loaded LightGBM Booster model.
    feature_df: Dataframe containing tabular features.
    feature_columns: Ordered list of feature names expected by the model.

  Returns:
    Predicted values as a NumPy array.
  """
  return model.predict(feature_df[feature_columns])


def inverse_scale_y(scaler: Any, scaled_arr: np.ndarray) -> np.ndarray:
  """Inverse-transform scaled sequence targets back to raw traffic volumes.

  Args:
    scaler: Fitted scaler object used during training data preparation.
    scaled_arr: Scaled target values.

  Returns:
    Inverse-scaled traffic volume values in original units.
  """
  dummy = np.zeros((len(scaled_arr), scaler.n_features_in_))
  dummy[:, 0] = scaled_arr
  return np.expm1(scaler.inverse_transform(dummy)[:, 0])


def build_sequence_context(
  filepath: Path,
  scaler: Any,
  label_encoder: Any,
) -> tuple[pd.DataFrame, np.ndarray]:
  """Build shared sequence features and metadata for sequence-model inference.

  Args:
    filepath: Path to the processed dataset used for prediction.
    scaler: Fitted scaler used to transform sequence tensors.
    label_encoder: Fitted label encoder for location-related categorical values.

  Returns:
    Tuple of results metadata dataframe and scaled sequence tensor.

  Raises:
    ValueError: If no valid sequences can be constructed.
  """
  df = read_processed_data(str(filepath))
  df = add_common_time_features(df)
  df["traffic_volume"] = np.log1p(df["traffic_volume"])
  df, _ = encode_road_names(df, label_encoder)

  x_all: list[np.ndarray] = []
  y_all: list[np.ndarray] = []
  meta_all: list[pd.DataFrame] = []

  for (_, _), group in df.groupby(["scats_number", "location"]):
    if len(group) < SEQ_LEN + FORECAST_HORIZON:
      continue

    features = group[SEQUENCE_FEATURE_COLUMNS].values
    x_seq, y_seq = create_sequences(features, SEQ_LEN, FORECAST_HORIZON)
    if len(x_seq) == 0:
      continue

    meta = group.iloc[SEQ_LEN: SEQ_LEN + len(x_seq)][
      ["datetime", "scats_number", "location", "hour", "day_of_week", "is_weekend"]
    ].reset_index(drop=True)
    x_all.append(x_seq)
    y_all.append(y_seq)
    meta_all.append(meta)

  if len(x_all) == 0:
    raise ValueError("No valid sequences found. Check dataset.")

  x = np.concatenate(x_all)
  y = np.concatenate(y_all)
  meta_df = pd.concat(meta_all, ignore_index=True)

  shape = x.shape
  x_scaled = scaler.transform(x.reshape(-1, shape[-1])).reshape(shape)
  y_scaled = scaler.transform(
    np.column_stack([y, np.zeros((len(y), scaler.n_features_in_ - 1))])
  )[:, 0]

  results_df = meta_df.copy()
  results_df["actual"] = inverse_scale_y(scaler, y_scaled)
  return results_df, x_scaled


def build_model_predictions(
  spec: dict[str, Any],
  filepath: Path,
  scaler: Any,
  label_encoder: Any,
  sequence_results: pd.DataFrame,
  x_scaled: np.ndarray,
  sequence_models: dict[str, tf.keras.Model] | None = None,
) -> pd.DataFrame | None:
  """Run one model spec and return predictions keyed by datetime/site/location.

  Args:
    spec: Model specification entry from MODEL_SPECS.
    filepath: Path to processed dataset used for optional tabular features.
    scaler: Fitted scaler used by sequence models.
    label_encoder: Fitted label encoder used for sequence preprocessing.
    sequence_results: Shared sequence metadata rows.
    x_scaled: Shared sequence tensor for sequence-model inference.
    sequence_models: Optional preloaded sequence model mapping.

  Returns:
    Prediction dataframe for one model, or None when artifact is unavailable.
  """
  del label_encoder
  model_path = Path(spec["path"])
  model_name = str(spec["name"])
  model_kind = str(spec["kind"])

  if not model_path.exists():
    LOGGER.warning("Model artifact is missing for %s: %s", model_name.upper(), model_path)
    return None

  LOGGER.info("Running inference with %s", model_name.upper())

  if model_kind == "sequence":
    if sequence_models is None or model_name not in sequence_models:
      raise ValueError(f"Sequence model '{model_name}' was not loaded.")

    model = sequence_models[model_name]
    y_pred_scaled = model.predict(x_scaled, verbose=0)
    predictions_df = sequence_results[["datetime", "scats_number", "location"]].copy()
    predictions_df[f"predicted_{model_name}"] = inverse_scale_y(scaler, y_pred_scaled.flatten())
    LOGGER.info("Completed inference with %s", model_name.upper())
    return predictions_df

  if model_kind == "tabular":
    metadata_path = Path(spec["metadata_path"])
    metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
    movement_df = load_movement_level_data(str(filepath))
    feature_df = create_tabular_sequences_by_movement(
      movement_df,
      int(metadata["sequence_length"]),
      int(metadata["forecast_horizon"]),
    )
    model = Booster(model_str=model_path.read_text(encoding="utf-8-sig"))
    predictions_df = feature_df[["datetime", "scats_number", "location"]].copy()
    predictions_df[f"predicted_{model_name}"] = predict_tabular_model(
      model,
      feature_df,
      metadata["feature_columns"],
    )
    LOGGER.info("Completed inference with %s", model_name.upper())
    return predictions_df

  LOGGER.warning("Unsupported model kind '%s' for spec '%s'", model_kind, model_name)
  return None


def build_predictions_table(
  filepath: Path,
  scaler: Any,
  label_encoder: Any,
  sequence_models: dict[str, tf.keras.Model] | None = None,
) -> pd.DataFrame:
  """Build one merged prediction table that includes all available model outputs.

  Args:
    filepath: Processed dataset path used for inference.
    scaler: Fitted scaler used for sequence feature normalization.
    label_encoder: Fitted label encoder for sequence context creation.
    sequence_models: Optional preloaded sequence model mapping.

  Returns:
    Merged prediction dataframe for all available model specs.
  """
  results_df, x_scaled = build_sequence_context(filepath, scaler, label_encoder)
  results_df["datetime"] = pd.to_datetime(results_df["datetime"])

  for spec in MODEL_SPECS:
    predictions_df = build_model_predictions(
      spec,
      filepath,
      scaler,
      label_encoder,
      results_df,
      x_scaled,
      sequence_models=sequence_models,
    )
    if predictions_df is None:
      continue

    predictions_df["datetime"] = pd.to_datetime(predictions_df["datetime"])
    results_df = results_df.merge(
      predictions_df,
      on=["datetime", "scats_number", "location"],
      how="left",
    )

  return results_df


def main() -> int:
  """Run batch inference and persist predictions CSV for a selected dataset.

  Returns:
    Process exit code where 0 indicates success.
  """
  logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")

  parser = argparse.ArgumentParser(description="Run model inference for prepared SCATS datasets.")
  parser.add_argument("--data", required=True, choices=["2006", "2014"], help="Dataset to predict on")
  args = parser.parse_args()

  LOGGER.info("Loading scaler and label encoder from 2006 preparation flow")
  (_, _), (_, _), (_, _), scaler, label_encoder = prepare_data(
    filepath=str(PROCESSED_DIR / "2006_processed.csv"),
    seq_len=SEQ_LEN,
    forecast_horizon=FORECAST_HORIZON,
  )

  LOGGER.info("Loading pre-trained LSTM/GRU artifacts from %s", MODEL_DIR)
  sequence_artifacts = load_sequence_model_artifacts(MODEL_DIR)
  sequence_models: dict[str, tf.keras.Model] = {
    "lstm": sequence_artifacts.lstm_model,
    "gru": sequence_artifacts.gru_model,
  }

  filepath = PROCESSED_DIR / f"{args.data}_processed.csv"
  if not filepath.exists():
    LOGGER.error("Dataset file not found: %s", filepath)
    return 1

  LOGGER.info("Running inference dataset load from %s", filepath)
  try:
    results_df = build_predictions_table(filepath, scaler, label_encoder, sequence_models=sequence_models)
  except ValueError as exc:
    LOGGER.error("Failed to build predictions: %s", exc)
    return 1

  PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
  output_path = PREDICTIONS_DIR / f"{args.data}_predictions.csv"
  results_df.to_csv(output_path, index=False)
  LOGGER.info("Predictions saved to %s", output_path)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
