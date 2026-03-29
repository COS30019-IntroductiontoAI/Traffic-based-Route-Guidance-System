import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, LabelEncoder

SEQUENCE_FEATURE_COLUMNS = [
  "traffic_volume",
  "hour",
  "day_of_week",
  "hour_sin",
  "hour_cos",
  "dow_sin",
  "dow_cos",
  "is_peak",
  "is_weekend",
  "road_name",
]

TABULAR_BASE_FEATURE_COLUMNS = [
  "scats_number",
  "location",
  "hour",
  "day_of_week",
  "is_weekend",
]

TABULAR_EXTRA_FEATURE_COLUMNS = [
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


# --------------------------------------
# --- Shared Data Preparation Helpers ---
# --------------------------------------

# Normalize minor schema differences between processed datasets.
def normalize_processed_schema(df: pd.DataFrame) -> pd.DataFrame:
  df = df.copy()
  if "nb_longtitude" in df.columns and "nb_longitude" not in df.columns:
    df = df.rename(columns={"nb_longtitude": "nb_longitude"})
  return df


# Parse processed datetime values consistently across loaders.
def parse_processed_datetime(values) -> pd.Series:
  datetime_strings = values.astype(str)
  iso_mask = datetime_strings.str.match(r"^\d{4}-\d{2}-\d{2}\s")
  slash_mask = datetime_strings.str.match(r"^\d{2}/\d{2}/\d{4}\s")

  parsed = pd.Series(pd.NaT, index=values.index, dtype="datetime64[ns]")
  if iso_mask.any():
    parsed.loc[iso_mask] = pd.to_datetime(datetime_strings.loc[iso_mask], format='ISO8601', errors="coerce")
  if slash_mask.any():
    parsed.loc[slash_mask] = pd.to_datetime(datetime_strings.loc[slash_mask], dayfirst=True, errors="coerce")

  remaining_mask = parsed.isna()
  if remaining_mask.any():
    parsed.loc[remaining_mask] = pd.to_datetime(datetime_strings.loc[remaining_mask], dayfirst=True, errors="coerce")

  return parsed


# Add shared cyclical time features used by both sequence and tabular models.
def add_common_time_features(df: pd.DataFrame) -> pd.DataFrame:
  df = df.copy()
  df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
  df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
  df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
  df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
  return df


# Read one processed CSV with a consistent schema and ordering.
def read_processed_data(filepath: str) -> pd.DataFrame:
  df = pd.read_csv(filepath)
  df = normalize_processed_schema(df)
  df["datetime"] = parse_processed_datetime(df["datetime"])
  df = df.dropna(subset=["datetime"])
  df = df.sort_values(["scats_number", "location", "datetime"]).reset_index(drop=True)
  return df


# Encode road_name with either a fresh encoder or an existing one.
def encode_road_names(
  df: pd.DataFrame,
  label_encoder: LabelEncoder | None = None,
) -> tuple[pd.DataFrame, LabelEncoder]:
  df = df.copy()
  if label_encoder is None:
    label_encoder = LabelEncoder()
    df["road_name"] = label_encoder.fit_transform(df["road_name"])
    return df, label_encoder

  known = set(label_encoder.classes_)
  df["road_name"] = df["road_name"].apply(
    lambda value: label_encoder.transform([value])[0] if value in known else -1
  )
  return df, label_encoder


# --------------------------------------
# ---   Sequence Model Helpers   ---
# --------------------------------------

# Build sliding window sequences for time series forecasting, ensuring that sequences do not cross group boundaries
def create_sequences(data: np.ndarray, seq_len: int, forecast_horizon: int): 
  X, y = [], []

  # Iterate through the data to create sequences of length seq_len and corresponding targets at forecast_horizon steps ahead
  for i in range(len(data) - seq_len - forecast_horizon + 1):
    X.append(data[i:i + seq_len])
    y.append(data[i + seq_len + forecast_horizon - 1, 0])  # target is traffic_volume

  return np.array(X), np.array(y)


# Split the sequences into train/validation/test sets based on specified ratios
def split_sequences(X: np.ndarray, y: np.ndarray, train_ratio: float = 0.7, val_ratio: float = 0.1):
  train_end = int(len(X) * train_ratio)
  val_end = int(len(X) * (train_ratio + val_ratio))

  X_train, y_train = X[:train_end], y[:train_end]
  X_val, y_val = X[train_end:val_end], y[train_end:val_end]
  X_test, y_test = X[val_end:], y[val_end:]

  return (X_train, y_train), (X_val, y_val), (X_test, y_test)


# Main function to prepare the data for training the models
def prepare_data(filepath, seq_len, forecast_horizon):
  df = read_processed_data(filepath)

  # Feature engineering: cyclic encoding for hour and day of week, log transformation for traffic_volume
  df = add_common_time_features(df)
  df["traffic_volume"] = np.log1p(df["traffic_volume"])
  
  # Encode road_name using label encoding
  df, label_encoder = encode_road_names(df)

  X_train_all, y_train_all = [], []
  X_val_all, y_val_all = [], []
  X_test_all, y_test_all = [], []

  # Create sequences for each (scats_number, location) group to ensure that sequences do not mix data from different groups
  for (scats, location), group in df.groupby(["scats_number", "location"]):
    if len(group) < seq_len + forecast_horizon:
      continue

    features = group[SEQUENCE_FEATURE_COLUMNS].values
    X_seq, y_seq = create_sequences(features, seq_len, forecast_horizon)

    if len(X_seq) == 0:
      continue

    # Split sequences into train/val/test sets for this group, then aggregate across groups
    (X_tr, y_tr), (X_v, y_v), (X_te, y_te) = split_sequences(X_seq, y_seq)

    X_train_all.append(X_tr); y_train_all.append(y_tr)
    X_val_all.append(X_v); y_val_all.append(y_v)
    X_test_all.append(X_te); y_test_all.append(y_te)

  X_train = np.concatenate(X_train_all)
  y_train = np.concatenate(y_train_all)
  X_val = np.concatenate(X_val_all)
  y_val = np.concatenate(y_val_all)
  X_test = np.concatenate(X_test_all)
  y_test = np.concatenate(y_test_all)

  # Scaler fit only on training data to prevent data leakage, then applied to all splits
  scaler = MinMaxScaler()
  scaler.fit(X_train.reshape(-1, X_train.shape[-1]))

  # Helper functions to scale the 3D input arrays and 1D target arrays using the fitted scaler
  def scale_X(arr):
    s = arr.shape
    return scaler.transform(arr.reshape(-1, s[-1])).reshape(s)

  # Helper function to scale the target variable using the same scaler
  def scale_y(arr):
    dummy = np.zeros((len(arr), scaler.n_features_in_))
    dummy[:, 0] = arr
    return scaler.transform(dummy)[:, 0]

  X_train = scale_X(X_train); y_train = scale_y(y_train)
  X_val = scale_X(X_val); y_val = scale_y(y_val)
  X_test = scale_X(X_test); y_test = scale_y(y_test)

  return (X_train, y_train), (X_val, y_val), (X_test, y_test), scaler, label_encoder


# --------------------------------------
# ---   Tabular Model Helpers   ---
# --------------------------------------

# Load movement-level rows and preserve time ordering inside each movement.
def load_movement_level_data(filepath: str) -> pd.DataFrame:
  df = read_processed_data(filepath)
  df = add_common_time_features(df)
  df["movement_id"] = df["scats_number"].astype(str) + " | " + df["location"].astype(str)
  return df


# Convert each movement history into one tabular row with lag features and engineered context.
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

      row["hour_sin"] = float(np.sin(2 * np.pi * row["hour"] / 24))
      row["hour_cos"] = float(np.cos(2 * np.pi * row["hour"] / 24))
      row["dow_sin"] = float(np.sin(2 * np.pi * row["day_of_week"] / 7))
      row["dow_cos"] = float(np.cos(2 * np.pi * row["day_of_week"] / 7))

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

      row["nb_latitude"] = float(target_row["nb_latitude"])
      row["nb_longitude"] = float(target_row["nb_longitude"])
      feature_rows.append(row)

  feature_df = pd.DataFrame(feature_rows)
  feature_df["scats_number"] = feature_df["scats_number"].astype("category")
  feature_df["location"] = feature_df["location"].astype("category")
  return feature_df


# Split tabular data chronologically by target timestamp.
def split_tabular_by_time(feature_df: pd.DataFrame, train_ratio: float = 0.7, val_ratio: float = 0.1):
  unique_times = feature_df["datetime"].sort_values().drop_duplicates().reset_index(drop=True)
  train_end_idx = int(len(unique_times) * train_ratio) - 1
  val_end_idx = int(len(unique_times) * (train_ratio + val_ratio)) - 1

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


# Prepare the movement-level tabular dataset and feature columns for LightGBM.
def prepare_tabular_data(filepath: str, seq_len: int, forecast_horizon: int):
  movement_df = load_movement_level_data(filepath)
  feature_df = create_tabular_sequences_by_movement(movement_df, seq_len, forecast_horizon)

  lag_feature_columns = [f"lag_{step}" for step in range(seq_len, 0, -1)]
  feature_columns = TABULAR_BASE_FEATURE_COLUMNS + lag_feature_columns + TABULAR_EXTRA_FEATURE_COLUMNS

  feature_df, train_df, val_df, test_df, train_end, val_end = split_tabular_by_time(feature_df)
  return feature_df, feature_columns, train_df, val_df, test_df, train_end, val_end
