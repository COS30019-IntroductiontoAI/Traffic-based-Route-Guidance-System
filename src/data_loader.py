import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from typing import Tuple


# Normalize the data using MinMaxScaler
def normalize_data(features: np.ndarray) -> Tuple[np.ndarray, MinMaxScaler]:
  # Define the scaler and fit it to the data
  scaler = MinMaxScaler()
  
  # Reshape the data to fit the scaler and transform it
  normalized_data = scaler.fit_transform(features)
  
  return normalized_data, scaler


# Create the sequences for training model
def create_sequences(data: np.ndarray, seq_len: int, forecast_horizon: int):
  X, y = [], []

  for i in range(len(data) - seq_len - forecast_horizon + 1):
    X.append(data[i:i + seq_len])
    y.append(data[i + seq_len + forecast_horizon - 1, 0]) 

  X = np.array(X)
  y = np.array(y)

  train_end = int(len(X) * 0.7)
  val_end = int(len(X) * 0.8)

  X_train, y_train = X[:train_end], y[:train_end]
  X_val, y_val = X[train_end:val_end], y[train_end:val_end]
  X_test, y_test = X[val_end:], y[val_end:]

  return (X_train, y_train), (X_val, y_val), (X_test, y_test)


# Main function to prepare the data for training the models
def prepare_data(filepath, seq_len, forecast_horizon):
  df = pd.read_csv(filepath, parse_dates=["datetime"], index_col="datetime")
  
  df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
  df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
  df["dow_sin"]  = np.sin(2 * np.pi * df["day_of_week"] / 7)
  df["dow_cos"]  = np.cos(2 * np.pi * df["day_of_week"] / 7)
  
  # log1p handles zeros safely, compresses spikes, lifts low values
  df["traffic_volume"] = np.log1p(df["traffic_volume"])
  
  features = df[["traffic_volume", "hour", "day_of_week", "is_weekend", "hour_sin", "hour_cos", "dow_sin", "dow_cos"]].values

  # Split into sequences and then normalize using the scaler fitted on the training data
  sequences = create_sequences(features, seq_len, forecast_horizon)
  (X_train, y_train), (X_val, y_val), (X_test, y_test) = sequences

  # Fit scaler on train rows only
  n_train = X_train.shape[0]
  scaler = MinMaxScaler()
  train_2d = features[:n_train + seq_len]   
  scaler.fit(train_2d)
  
  # Transform all splits using the train-fitted scaler
  def scale_X(X):
    shape = X.shape
    return scaler.transform(X.reshape(-1, shape[-1])).reshape(shape)
  
  X_train = scale_X(X_train)
  X_val   = scale_X(X_val)
  X_test  = scale_X(X_test)
  
  # Scale y values using only feature 0 (traffic_volume)
  dummy = np.zeros((len(y_train), scaler.n_features_in_))
  dummy[:, 0] = y_train
  y_train = scaler.transform(dummy)[:, 0] 
  dummy = np.zeros((len(y_val), scaler.n_features_in_))
  dummy[:, 0] = y_val
  y_val = scaler.transform(dummy)[:, 0]
  dummy = np.zeros((len(y_test), scaler.n_features_in_))
  dummy[:, 0] = y_test
  y_test = scaler.transform(dummy)[:, 0]

  return (X_train, y_train), (X_val, y_val), (X_test, y_test), scaler
