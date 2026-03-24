import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from tensorflow.keras.models import load_model
from src.data_loader import prepare_data, create_sequences
from src.model_config import SEQ_LEN, FORECAST_HORIZON

PROCESSED_DIR = Path("data/processed")
PREDICTIONS_DIR = Path("results/predictions")
MODEL_DIR = Path("results/trained_models")

MODELS = [
  ("lstm", MODEL_DIR / "lstm_model.keras"),
  ("gru",  MODEL_DIR / "gru_model.keras"),
]


def main():
  # Parse command line arguments
  parser = argparse.ArgumentParser()
  parser.add_argument("--data", required=True, choices=["2006", "2014"], help="Dataset to predict on")
  args = parser.parse_args()



  # ---------------------------------------------
  # --- 1. LOAD 2006 SCALER AND LABEL ENCODER ---
  # ---------------------------------------------
  print("Loading 2006 scaler and label encoder...")
  (_, _), (_, _), (_, _), scaler, label_encoder = prepare_data(
    filepath=str(PROCESSED_DIR / "2006_processed.csv"),
    seq_len=SEQ_LEN,
    forecast_horizon=FORECAST_HORIZON
  )



  # ---------------------------------
  # --- 2. LOAD THE TARGET DATASET ---
  # ---------------------------------
  filepath = PROCESSED_DIR / f"{args.data}_processed.csv"
  if not filepath.exists():
    print(f"Error: Dataset file '{filepath}' not found.")
    return

  print(f"Loading {filepath}...")
  df = pd.read_csv(filepath, parse_dates=["datetime"])
  df = df.sort_values(["scats_number", "location", "datetime"])



  # -----------------------------------------
  # --- 3. APPLY SAME FEATURE ENGINEERING ---
  # -----------------------------------------
  df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
  df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
  df["dow_sin"]  = np.sin(2 * np.pi * df["day_of_week"] / 7)
  df["dow_cos"]  = np.cos(2 * np.pi * df["day_of_week"] / 7)
  df["traffic_volume"] = np.log1p(df["traffic_volume"])

  # Apply 2006 label encoder (transform only, unknown road names → -1)
  known = list(label_encoder.classes_)
  df["road_name"] = df["road_name"].apply(
    lambda x: label_encoder.transform([x])[0] if x in known else -1
  )

  feature_cols = [
    "traffic_volume", "hour", "day_of_week", "hour_sin", "hour_cos",
    "dow_sin", "dow_cos", "is_peak", "is_weekend", "road_name"
  ]



  # ----------------------------------------------------------------
  # --- 4. BUILD SEQUENCES AND TRACK METADATA PER GROUP          ---
  # --- Each prediction is tagged with its datetime and metadata ---
  # ----------------------------------------------------------------
  X_all, y_all = [], []
  meta_all = []

  for (scats, location), group in df.groupby(["scats_number", "location"]):
    if len(group) < SEQ_LEN + FORECAST_HORIZON:
      continue

    features = group[feature_cols].values
    X_seq, y_seq = create_sequences(features, SEQ_LEN, FORECAST_HORIZON)

    if len(X_seq) == 0:
      continue

    # The predicted timestep for sequence i is at index i + SEQ_LEN in the group
    # So metadata spans from group row SEQ_LEN to the end
    meta = group.iloc[SEQ_LEN: SEQ_LEN + len(X_seq)][
      ["datetime", "scats_number", "location", "hour", "day_of_week", "is_weekend"]
    ].reset_index(drop=True)

    X_all.append(X_seq)
    y_all.append(y_seq)
    meta_all.append(meta)

  if len(X_all) == 0:
    print("Error: No valid sequences found. Check dataset.")
    return

  X = np.concatenate(X_all)
  y = np.concatenate(y_all)
  meta_df = pd.concat(meta_all, ignore_index=True)



  # -------------------------------------------------
  # --- 5. SCALE USING 2006 SCALER (NO REFITTING) ---
  # -------------------------------------------------
  def scale_X(arr):
    s = arr.shape
    return scaler.transform(arr.reshape(-1, s[-1])).reshape(s)

  def scale_y(arr):
    dummy = np.zeros((len(arr), scaler.n_features_in_))
    dummy[:, 0] = arr
    return scaler.transform(dummy)[:, 0]

  def inverse_scale_y(scaled_arr):
    dummy = np.zeros((len(scaled_arr), scaler.n_features_in_))
    dummy[:, 0] = scaled_arr
    return np.expm1(scaler.inverse_transform(dummy)[:, 0])

  X_scaled = scale_X(X)
  y_scaled  = scale_y(y)
  actual    = inverse_scale_y(y_scaled)



  # ------------------------------------------------------
  # --- 6. PREDICT WITH EACH MODEL AND COLLECT RESULTS ---
  # ------------------------------------------------------
  PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
  results_df = meta_df.copy()
  results_df["actual"] = actual

  for model_name, model_path in MODELS:
    if not model_path.exists():
      print(f"Warning: {model_path} not found, skipping {model_name.upper()}.")
      continue

    print(f"Predicting with {model_name.upper()}...")
    model = load_model(model_path)
    y_pred_scaled = model.predict(X_scaled)
    predicted = inverse_scale_y(y_pred_scaled.flatten())
    results_df[f"predicted_{model_name}"] = predicted
    print(f"{model_name.upper()} done.")



  # ----------------------------------
  # --- 7. SAVE PREDICTIONS TO CSV ---
  # ----------------------------------
  output_path = PREDICTIONS_DIR / f"{args.data}_predictions.csv"
  results_df.to_csv(output_path, index=False)
  print(f"\nPredictions saved → {output_path}")


if __name__ == "__main__":
  main()