import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from typing import Tuple


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