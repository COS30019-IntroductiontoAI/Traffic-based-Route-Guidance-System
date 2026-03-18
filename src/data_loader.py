import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler


# -----------------------------------------
# --- Sequence-Based Model Data Helpers ---
# -----------------------------------------

# Build sliding window sequences for time series forecasting.
def create_sequences(data: np.ndarray, seq_len: int, forecast_horizon: int):
  X, y = [], []

  # Create one input window and one target for each valid time step.
  for i in range(len(data) - seq_len - forecast_horizon + 1):
    X.append(data[i:i + seq_len])
    y.append(data[i + seq_len + forecast_horizon - 1, 0])

  return np.array(X), np.array(y)


# Split a prepared sequence set into train, validation, and test partitions.
def split_sequences(X: np.ndarray, y: np.ndarray, train_ratio: float = 0.7, val_ratio: float = 0.1):
  train_end = int(len(X) * train_ratio)
  val_end = int(len(X) * (train_ratio + val_ratio))

  X_train, y_train = X[:train_end], y[:train_end]
  X_val, y_val = X[train_end:val_end], y[train_end:val_end]
  X_test, y_test = X[val_end:], y[val_end:]

  return (X_train, y_train), (X_val, y_val), (X_test, y_test)


# Prepare grouped movement-level sequences for the LSTM and GRU models.
def prepare_data(filepath, seq_len, forecast_horizon):
  df = pd.read_csv(filepath, parse_dates=["datetime"])
  df = df.sort_values(["scats_number", "location", "datetime"])

  # Encode cyclic time features and compress traffic spikes with log1p.
  df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
  df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
  df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
  df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
  df["traffic_volume"] = np.log1p(df["traffic_volume"])

  feature_cols = ["traffic_volume", "hour", "day_of_week", "hour_sin", "hour_cos", "dow_sin", "dow_cos"]

  X_train_all, y_train_all = [], []
  X_val_all, y_val_all = [], []
  X_test_all, y_test_all = [], []

  # Keep each movement as its own time series so sequences do not cross movement boundaries.
  for (_, _), group in df.groupby(["scats_number", "location"]):
    if len(group) < seq_len + forecast_horizon:
      continue

    features = group[feature_cols].values
    X_seq, y_seq = create_sequences(features, seq_len, forecast_horizon)

    if len(X_seq) == 0:
      continue

    (X_tr, y_tr), (X_v, y_v), (X_te, y_te) = split_sequences(X_seq, y_seq)
    X_train_all.append(X_tr)
    y_train_all.append(y_tr)
    X_val_all.append(X_v)
    y_val_all.append(y_v)
    X_test_all.append(X_te)
    y_test_all.append(y_te)

  X_train = np.concatenate(X_train_all)
  y_train = np.concatenate(y_train_all)
  X_val = np.concatenate(X_val_all)
  y_val = np.concatenate(y_val_all)
  X_test = np.concatenate(X_test_all)
  y_test = np.concatenate(y_test_all)

  # Fit the scaler on train rows only to avoid leakage.
  scaler = MinMaxScaler()
  scaler.fit(X_train.reshape(-1, X_train.shape[-1]))

  # Scale 3D sequence arrays with the same feature-wise scaler.
  def scale_X(arr):
    shape = arr.shape
    return scaler.transform(arr.reshape(-1, shape[-1])).reshape(shape)

  # Scale the 1D target through the traffic feature slot.
  def scale_y(arr):
    dummy = np.zeros((len(arr), scaler.n_features_in_))
    dummy[:, 0] = arr
    return scaler.transform(dummy)[:, 0]

  X_train = scale_X(X_train)
  y_train = scale_y(y_train)
  X_val = scale_X(X_val)
  y_val = scale_y(y_val)
  X_test = scale_X(X_test)
  y_test = scale_y(y_test)

  return (X_train, y_train), (X_val, y_val), (X_test, y_test), scaler


# ----------------------------------
# --- Tabular Model Data Helper ---
# ----------------------------------

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

      # Encode repeated time patterns so the model can capture daily and weekly cycles.
      row["hour_sin"] = float(np.sin(2 * np.pi * row["hour"] / 24))
      row["hour_cos"] = float(np.cos(2 * np.pi * row["hour"] / 24))
      row["dow_sin"] = float(np.sin(2 * np.pi * row["day_of_week"] / 7))
      row["dow_cos"] = float(np.cos(2 * np.pi * row["day_of_week"] / 7))

      # Summarize the recent history window instead of relying only on raw lag columns.
      row["recent_mean_4"] = float(history_window[-4:].mean())
      row["recent_mean_8"] = float(history_window[-8:].mean())
      row["recent_mean_16"] = float(history_window[-16:].mean())
      row["recent_std_4"] = float(history_window[-4:].std())
      row["recent_std_8"] = float(history_window[-8:].std())
      row["recent_min_8"] = float(history_window[-8:].min())
      row["recent_max_8"] = float(history_window[-8:].max())
      row["lag_diff_1"] = float(history_window[-1] - history_window[-2])
      row["lag_diff_4"] = float(history_window[-1] - history_window[-4])
      row["lag_diff_8"] = float(history_window[-1] - history_window[-8])

      # Keep the movement coordinates so the model can learn stable spatial differences.
      row["nb_latitude"] = float(target_row["nb_latitude"])
      row["nb_longitude"] = float(target_row["nb_longitude"])

      feature_rows.append(row)

  feature_df = pd.DataFrame(feature_rows)
  feature_df["scats_number"] = feature_df["scats_number"].astype("category")
  feature_df["location"] = feature_df["location"].astype("category")
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
def prepare_tabular_data(filepath: str, seq_len: int, forecast_horizon: int):
  movement_df = load_movement_level_data(filepath)
  feature_df = create_tabular_sequences_by_movement(movement_df, seq_len, forecast_horizon)

  base_feature_columns = [
    "scats_number",
    "location",
    "hour",
    "day_of_week",
    "is_weekend",
  ]
  lag_feature_columns = [f"lag_{step}" for step in range(seq_len, 0, -1)]
  extra_feature_columns = [
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
    "recent_mean_4",
    "recent_mean_8",
    "recent_mean_16",
    "recent_std_4",
    "recent_std_8",
    "recent_min_8",
    "recent_max_8",
    "lag_diff_1",
    "lag_diff_4",
    "lag_diff_8",
    "nb_latitude",
    "nb_longitude",
  ]
  feature_columns = base_feature_columns + lag_feature_columns + extra_feature_columns

  feature_df, train_df, val_df, test_df, train_end, val_end = split_tabular_by_time(feature_df)
  return feature_df, feature_columns, train_df, val_df, test_df, train_end, val_end
