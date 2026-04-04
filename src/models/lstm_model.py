"""LSTM training module for SCATS traffic forecasting.

This module exposes reusable, typed training utilities so that importing it does
not trigger model training or data loading side effects.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import tensorflow as tf
from src.config.model_config import (
  BATCH_SIZE,
  DROPOUT_RATE,
  EARLY_STOP_PATIENCE,
  EPOCHS,
  FORECAST_HORIZON,
  INPUT_FEATURES,
  L2_REG,
  LEARNING_RATE,
  LR_REDUCE_FACTOR,
  LR_REDUCE_PATIENCE,
  MIN_LR,
  MONITOR_METRIC,
  SEQ_LEN,
)
from src.data_loader import prepare_data

SRC_ROOT: Path = Path(__file__).resolve().parents[1]
PROCESSED_2006_PATH: Path = SRC_ROOT / "data" / "processed" / "2006_processed.csv"
TRAINED_MODELS_DIR: Path = SRC_ROOT / "results" / "trained_models"
GRAPHS_DIR: Path = SRC_ROOT / "results" / "graphs"


def build_lstm_model(
  seq_len: int,
  input_features: int,
  learning_rate: float,
  dropout_rate: float,
  l2_reg: float,
) -> tf.keras.Model:
  """Build and compile the LSTM forecasting model.

  Args:
    seq_len: Number of historical timesteps used for each input sequence.
    input_features: Number of input features at each timestep.
    learning_rate: Adam optimizer learning rate.
    dropout_rate: Dropout probability applied after recurrent blocks.
    l2_reg: L2 regularization factor used in recurrent and dense layers.

  Returns:
    A compiled TensorFlow Keras model ready for training.
  """
  model = tf.keras.Sequential(
    [
      tf.keras.layers.LSTM(
        units=128,
        return_sequences=True,
        input_shape=(seq_len, input_features),
        kernel_regularizer=tf.keras.regularizers.l2(l2_reg),
        recurrent_regularizer=tf.keras.regularizers.l2(l2_reg),
      ),
      tf.keras.layers.Dropout(dropout_rate),
      tf.keras.layers.LSTM(
        units=64,
        return_sequences=True,
        kernel_regularizer=tf.keras.regularizers.l2(l2_reg),
        recurrent_regularizer=tf.keras.regularizers.l2(l2_reg),
      ),
      tf.keras.layers.Dropout(dropout_rate),
      tf.keras.layers.LSTM(
        units=32,
        return_sequences=False,
        kernel_regularizer=tf.keras.regularizers.l2(l2_reg),
        recurrent_regularizer=tf.keras.regularizers.l2(l2_reg),
      ),
      tf.keras.layers.Dense(
        units=32,
        activation="relu",
        kernel_regularizer=tf.keras.regularizers.l2(l2_reg),
      ),
      tf.keras.layers.Dense(units=1),
    ]
  )
  model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
    loss="mae",
    metrics=["mae", "mape"],
  )
  return model


def create_training_callbacks(
  model_output_path: Path,
  monitor_metric: str,
  early_stop_patience: int,
  lr_reduce_factor: float,
  lr_reduce_patience: int,
  min_lr: float,
) -> list[tf.keras.callbacks.Callback]:
  """Create training callbacks for regularized and stable optimization.

  Args:
    model_output_path: Destination path for saving the best model checkpoint.
    monitor_metric: Validation metric name used by callbacks.
    early_stop_patience: Epoch count to wait before early stopping.
    lr_reduce_factor: Multiplicative factor for learning-rate reduction.
    lr_reduce_patience: Epoch count to wait before reducing learning rate.
    min_lr: Lower bound for the learning rate.

  Returns:
    A list of configured Keras callbacks.
  """
  return [
    tf.keras.callbacks.EarlyStopping(
      monitor=monitor_metric,
      patience=early_stop_patience,
      restore_best_weights=True,
      mode="min",
    ),
    tf.keras.callbacks.ReduceLROnPlateau(
      monitor=monitor_metric,
      factor=lr_reduce_factor,
      patience=lr_reduce_patience,
      min_lr=min_lr,
      verbose=1,
    ),
    tf.keras.callbacks.ModelCheckpoint(
      filepath=str(model_output_path),
      monitor=monitor_metric,
      save_best_only=True,
      mode="min",
    ),
  ]


def plot_training_curve(
  history: tf.keras.callbacks.History,
  output_path: Path,
  title: str,
) -> None:
  """Persist training and validation loss curves for non-interactive environments.

  Args:
    history: Keras fit history returned from model training.
    output_path: File path where the chart image will be saved.
    title: Plot title shown in the saved figure.
  """
  plt.figure(figsize=(10, 6))
  plt.plot(history.history.get("loss", []), label="Training Loss")
  plt.plot(history.history.get("val_loss", []), label="Validation Loss")
  plt.title(title)
  plt.xlabel("Epochs")
  plt.ylabel("Loss")
  plt.legend()
  output_path.parent.mkdir(parents=True, exist_ok=True)
  plt.savefig(output_path)
  plt.close()


def train_lstm_model(
  data_path: Path = PROCESSED_2006_PATH,
  model_dir: Path = TRAINED_MODELS_DIR,
  graphs_dir: Path = GRAPHS_DIR,
  seq_len: int = SEQ_LEN,
  forecast_horizon: int = FORECAST_HORIZON,
  input_features: int = INPUT_FEATURES,
  epochs: int = EPOCHS,
  batch_size: int = BATCH_SIZE,
  learning_rate: float = LEARNING_RATE,
  dropout_rate: float = DROPOUT_RATE,
  l2_reg: float = L2_REG,
  monitor_metric: str = MONITOR_METRIC,
  early_stop_patience: int = EARLY_STOP_PATIENCE,
  lr_reduce_patience: int = LR_REDUCE_PATIENCE,
  lr_reduce_factor: float = LR_REDUCE_FACTOR,
  min_lr: float = MIN_LR,
) -> tf.keras.Model:
  """Train an LSTM model using project defaults or caller-provided overrides.

  Args:
    data_path: Path to processed training CSV data.
    model_dir: Directory where model checkpoint artifacts are saved.
    graphs_dir: Directory where training curves are saved.
    seq_len: Number of historical timesteps per training sample.
    forecast_horizon: Forecast horizon used by the data loader.
    input_features: Number of input features per timestep.
    epochs: Maximum number of training epochs.
    batch_size: Mini-batch size for gradient descent.
    learning_rate: Initial Adam learning rate.
    dropout_rate: Dropout rate applied between recurrent layers.
    l2_reg: L2 regularization factor.
    monitor_metric: Validation metric to monitor for callbacks.
    early_stop_patience: Early stopping patience.
    lr_reduce_patience: Learning-rate reduction patience.
    lr_reduce_factor: Learning-rate reduction factor.
    min_lr: Minimum learning rate after reductions.

  Returns:
    The trained LSTM model with best weights restored.
  """
  model_dir.mkdir(parents=True, exist_ok=True)
  (train_split, val_split, _test_split, _scaler, _label_encoder) = prepare_data(
    str(data_path),
    seq_len=seq_len,
    forecast_horizon=forecast_horizon,
  )
  x_train, y_train = train_split
  x_val, y_val = val_split

  model = build_lstm_model(
    seq_len=seq_len,
    input_features=input_features,
    learning_rate=learning_rate,
    dropout_rate=dropout_rate,
    l2_reg=l2_reg,
  )
  callbacks = create_training_callbacks(
    model_output_path=model_dir / "lstm_model.keras",
    monitor_metric=monitor_metric,
    early_stop_patience=early_stop_patience,
    lr_reduce_factor=lr_reduce_factor,
    lr_reduce_patience=lr_reduce_patience,
    min_lr=min_lr,
  )
  history: tf.keras.callbacks.History = model.fit(
    x_train,
    y_train,
    validation_data=(x_val, y_val),
    epochs=epochs,
    batch_size=batch_size,
    callbacks=callbacks,
    shuffle=True,
  )
  plot_training_curve(
    history=history,
    output_path=graphs_dir / "lstm_training_curve.png",
    title="LSTM Model Training and Validation Loss",
  )
  return model


def main() -> None:
  """Train the LSTM model when the module is run as a script."""
  trained_model = train_lstm_model()
  trained_model.summary()


if __name__ == "__main__":
  main()
