import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from typing import Tuple


# -----------------------------------------
# --- Sequence-Based Model Data Helpers ---
# -----------------------------------------

# Normalize the data using MinMaxScaler
def normalize_data(series: np.ndarray) -> Tuple[np.ndarray, MinMaxScaler]:
  # Define the scaler and fit it to the data
  scaler = MinMaxScaler()
  
  # Reshape the data to fit the scaler and transform it
  normalized_data = scaler.fit_transform(series.values.reshape(-1, 1))
  
  return normalized_data, scaler


# Create the sequences for training model
def create_sequences(data: np.ndarray, seq_len: int, forecast_horizon: int):
  X, y = [], []
  
  # Loop through the data to create sequences of the specified length and corresponding targets
  for i in range(len(data) - seq_len - forecast_horizon + 1):
    X.append(data[i:i + seq_len])
    y.append(data[i + seq_len + forecast_horizon - 1])
    
  X = np.array(X)
  y = np.array(y)
  
  # 70% for training, 10% for validation, and 20% for testing
  train_end = int(len(X) * 0.7)
  val_end = int(len(X) * 0.8)
  
  # Split the data into training, validation, and testing sets
  X_train, y_train = X[:train_end], y[:train_end]
  X_val, y_val = X[train_end:val_end], y[train_end:val_end]
  X_test, y_test = X[val_end:], y[val_end:]
  
  return (X_train, y_train), (X_val, y_val), (X_test, y_test)


# Main function to prepare the data for training the models
def prepare_data(filepath: str, seq_len: int, forecast_horizon: int):
  # Load the data from the processed csv file
  df = pd.read_csv(filepath, parse_dates=["datetime"], index_col="datetime")
  series = df["traffic_volume"]
  
  # Normalize the data
  scaled, scaler = normalize_data(series)

  # Create the sequences for training, validation, and testing
  (X_train, y_train), (X_val, y_val), (X_test, y_test) = create_sequences(scaled, seq_len, forecast_horizon)
  
  return (X_train, y_train), (X_val, y_val), (X_test, y_test), scaler


# -----------------------------------
# --- XGBoost Tabular Data Helper ---
# -----------------------------------

# Load the processed traffic rows and keep the movement-level ordering intact.
def load_movement_level_data(filepath: str) -> pd.DataFrame:
  df = pd.read_csv(filepath, parse_dates=["datetime"])
  df = df.sort_values(["scats_number", "location", "datetime"]).reset_index(drop=True)
  df["movement_id"] = df["scats_number"].astype(str) + " | " + df["location"]
  return df

# Convert each movement sequence into a tabular training row using lag values as columns.
def create_tabular_sequences_by_movement(df: pd.DataFrame, seq_len: int, forecast_horizon: int) -> pd.DataFrame:
  feature_rows = []

  for (_, _), group_df in df.groupby(["scats_number", "location"], sort=False):
    group_df = group_df.sort_values("datetime").reset_index(drop=True)
    traffic_values = group_df["traffic_volume"].to_numpy(dtype=float)

    for start_idx in range(len(group_df) - seq_len - forecast_horizon + 1):
      history_window = traffic_values[start_idx:start_idx + seq_len]
      target_idx = start_idx + seq_len + forecast_horizon - 1
      target_row = group_df.iloc[target_idx]

      row = {
        "scats_number": int(target_row["scats_number"]),
        "location": target_row["location"],
        "movement_id": target_row["movement_id"],
        "datetime": target_row["datetime"],
        "hour": int(target_row["hour"]),
        "day_of_week": int(target_row["day_of_week"]),
        "is_weekend": int(target_row["is_weekend"]),
        "traffic_volume": float(target_row["traffic_volume"]),
      }

      for lag_step, lag_value in zip(range(seq_len, 0, -1), history_window):
        row[f"lag_{lag_step}"] = float(lag_value)

      feature_rows.append(row)

  feature_df = pd.DataFrame(feature_rows)
  feature_df["movement_code"] = feature_df["movement_id"].astype("category").cat.codes
  return feature_df


# Split the tabular data by chronological target timestamps.
def split_tabular_by_time(feature_df: pd.DataFrame):
  unique_times = feature_df["datetime"].sort_values().drop_duplicates().reset_index(drop=True)
  train_end_idx = int(len(unique_times) * 0.7) - 1
  val_end_idx = int(len(unique_times) * 0.8) - 1

  train_end_idx = max(train_end_idx, 0)
  val_end_idx = min(max(val_end_idx, train_end_idx + 1), len(unique_times) - 1)

  train_end = unique_times.iloc[train_end_idx]
  val_end = unique_times.iloc[val_end_idx]

  train_df = feature_df[feature_df["datetime"] <= train_end].copy()
  val_df = feature_df[
    (feature_df["datetime"] > train_end) & (feature_df["datetime"] <= val_end)
  ].copy()
  test_df = feature_df[feature_df["datetime"] > val_end].copy()

  return feature_df, train_df, val_df, test_df, train_end, val_end


# Prepare the movement-level tabular dataset and feature column list.
def prepare_xgboost_data(filepath: str, seq_len: int, forecast_horizon: int):
  movement_df = load_movement_level_data(filepath)
  feature_df = create_tabular_sequences_by_movement(movement_df, seq_len, forecast_horizon)

  base_feature_columns = [
    "scats_number",
    "movement_code",
    "hour",
    "day_of_week",
    "is_weekend",
  ]
  lag_feature_columns = [f"lag_{step}" for step in range(seq_len, 0, -1)]
  feature_columns = base_feature_columns + lag_feature_columns

  feature_df, train_df, val_df, test_df, train_end, val_end = split_tabular_by_time(feature_df)
  return feature_df, feature_columns, train_df, val_df, test_df, train_end, val_end
