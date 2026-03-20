import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, LabelEncoder


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
  df = pd.read_csv(filepath, parse_dates=["datetime"])
  df = df.sort_values(["scats_number", "location", "datetime"])

  # Feature engineering: cyclic encoding for hour and day of week, log transformation for traffic_volume
  df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
  df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
  df["dow_sin"]  = np.sin(2 * np.pi * df["day_of_week"] / 7)
  df["dow_cos"]  = np.cos(2 * np.pi * df["day_of_week"] / 7)
  df["traffic_volume"] = np.log1p(df["traffic_volume"])
  
  # Encode road_name using label encoding
  label_encoder = LabelEncoder()
  df["road_name"] = label_encoder.fit_transform(df["road_name"])

  # Define the feature columns to be used for modeling
  feature_cols = ["traffic_volume", "hour", "day_of_week", "hour_sin", "hour_cos", "dow_sin", "dow_cos", "is_peak", "is_weekend", "road_name"]

  X_train_all, y_train_all = [], []
  X_val_all, y_val_all = [], []
  X_test_all, y_test_all = [], []

  # Create sequences for each (scats_number, location) group to ensure that sequences do not mix data from different groups
  for (scats, location), group in df.groupby(["scats_number", "location"]):
    if len(group) < seq_len + forecast_horizon:
      continue

    features = group[feature_cols].values
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

  return (X_train, y_train), (X_val, y_val), (X_test, y_test), scaler 