import numpy as np
import matplotlib.pyplot as plt 
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.losses import Huber
from src.data_loader import prepare_data
from src.model_config import (
  SEQ_LEN,
  FORECAST_HORIZON,
  INPUT_FEATURES,
  EPOCHS,
  BATCH_SIZE,
  LEARNING_RATE,
  DROPOUT_RATE,
  EARLY_STOP_PATIENCE,
  LR_REDUCE_PATIENCE,
  LR_REDUCE_FACTOR,
  MIN_LR,
)


# ------------------------------------
# --- 1. LOAD AND PREPARE THE DATA ---
# ------------------------------------
(X_train, y_train), (X_val, y_val), (X_test, y_test), scaler = prepare_data(
  "data/processed/processed_traffic.csv",
  seq_len=SEQ_LEN,
  forecast_horizon=FORECAST_HORIZON
)


# -------------------------------
# --- 2. BUILD THE LSTM MODEL ---
# -------------------------------
model = Sequential([
  LSTM(units=128, return_sequences=True, input_shape=(SEQ_LEN, INPUT_FEATURES)),
  Dropout(DROPOUT_RATE),
  LSTM(units=64, return_sequences=True),
  Dropout(DROPOUT_RATE),
  LSTM(units=32, return_sequences=False),
  Dense(units=32, activation="relu"),
  Dense(units=1)
])

optimizer = Adam(learning_rate=LEARNING_RATE)

# Huber loss is less sensitive to outliers than MSE, which is beneficial for traffic data with spikes
model.compile(
  optimizer=optimizer,
  loss=Huber(),
  metrics=["mae", "mape"]
)
model.summary()


# --------------------
# --- 3. CALLBACKS ---
# --------------------
early_stop = EarlyStopping(
  monitor="val_loss",
  patience=EARLY_STOP_PATIENCE,
  restore_best_weights=True
)

# Reduce learning rate when validation loss plateaus
reduce_lr = ReduceLROnPlateau(
  monitor="val_loss",
  factor=LR_REDUCE_FACTOR,
  patience=LR_REDUCE_PATIENCE,
  min_lr=MIN_LR,
  verbose=1
)

# Save the best model based on validation loss
checkpoint = ModelCheckpoint(
  "results/trained_models/lstm_model.keras", 
  monitor="val_loss",
  save_best_only=True,
  mode="min"
)


# --------------------------
# --- 4. TRAIN THE MODEL ---
# --------------------------
history = model.fit(
  X_train, y_train,
  validation_data=(X_val, y_val),
  epochs=EPOCHS,
  batch_size=BATCH_SIZE,
  callbacks=[early_stop, reduce_lr, checkpoint],
  shuffle=True
)


# ------------------------------
# --- 5. PLOT TRAINING CURVE ---
# ------------------------------
plt.figure(figsize=(10, 6))
plt.plot(history.history["loss"], label="Training Loss")
plt.plot(history.history["val_loss"], label="Validation Loss")
plt.title("LSTM Model Training and Validation Loss")
plt.xlabel("Epochs")
plt.ylabel("Loss")
plt.legend()
plt.savefig("results/trained_models/lstm_training_curve.png")
plt.show()
