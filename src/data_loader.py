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
def prepare_data(filepath: str, seq_len: int, forecast_horizon: int):
  # Load the data from the processed csv file
  df = pd.read_csv(filepath, parse_dates=["datetime"], index_col="datetime")
  
  # Add cyclical encodings for hour/day to better capture periodicity
  df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
  df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
  df["dow_sin"]  = np.sin(2 * np.pi * df["day_of_week"] / 7)
  df["dow_cos"]  = np.cos(2 * np.pi * df["day_of_week"] / 7)
  
  # Select the relevant features for modeling
  features = df[["traffic_volume", "hour", "day_of_week", "is_weekend", "hour_sin", "hour_cos", "dow_sin", "dow_cos"]].values
  
  # Normalize the data
  scaled, scaler = normalize_data(features)

  # Create the sequences for training, validation, and testing
  (X_train, y_train), (X_val, y_val), (X_test, y_test) = create_sequences(scaled, seq_len, forecast_horizon)
  
  return (X_train, y_train), (X_val, y_val), (X_test, y_test), scaler
