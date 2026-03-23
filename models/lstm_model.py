import numpy as np
import matplotlib.pyplot as plt 
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras import regularizers
from src.data_loader import prepare_data
from src.model_config import (
  SEQ_LEN,
  FORECAST_HORIZON,
  INPUT_FEATURES,
  EPOCHS,
  BATCH_SIZE,
  LEARNING_RATE,
  DROPOUT_RATE,
  L2_REG,
  EARLY_STOP_PATIENCE,
  LR_REDUCE_PATIENCE,
  LR_REDUCE_FACTOR,
  MIN_LR,
  MONITOR_METRIC,
)


# ------------------------------------
# --- 1. LOAD AND PREPARE THE DATA ---
# ------------------------------------
(X_train, y_train), (X_val, y_val), (X_test, y_test), scaler = prepare_data(
  "data/processed/2006_processed.csv",
  seq_len=SEQ_LEN,
  forecast_horizon=FORECAST_HORIZON
)


# -------------------------------
# --- 2. BUILD THE LSTM MODEL ---
# -------------------------------
model = Sequential([
  LSTM(
    units=128,
    return_sequences=True,
    input_shape=(SEQ_LEN, INPUT_FEATURES),
    kernel_regularizer=regularizers.l2(L2_REG),
    recurrent_regularizer=regularizers.l2(L2_REG),
  ),
  Dropout(DROPOUT_RATE),
  LSTM(
    units=64,
    return_sequences=True,
    kernel_regularizer=regularizers.l2(L2_REG),
    recurrent_regularizer=regularizers.l2(L2_REG),
  ),
  Dropout(DROPOUT_RATE),
  LSTM(
    units=32,
    return_sequences=False,
    kernel_regularizer=regularizers.l2(L2_REG),
    recurrent_regularizer=regularizers.l2(L2_REG),
  ),
  Dense(units=32, activation="relu", kernel_regularizer=regularizers.l2(L2_REG)),
  Dense(units=1)
])

optimizer = Adam(learning_rate=LEARNING_RATE)

# Use MAE loss to better align optimization with MAPE while remaining stable on low-volume periods
model.compile(optimizer=optimizer, loss="mae", metrics=["mae", "mape"])
model.summary()


# --------------------
# --- 3. CALLBACKS ---
# --------------------
early_stop = EarlyStopping(
  monitor=MONITOR_METRIC,
  patience=EARLY_STOP_PATIENCE,
  restore_best_weights=True,
  mode="min"
)

# Reduce learning rate when validation loss plateaus
reduce_lr = ReduceLROnPlateau(
  monitor=MONITOR_METRIC,
  factor=LR_REDUCE_FACTOR,
  patience=LR_REDUCE_PATIENCE,
  min_lr=MIN_LR,
  verbose=1
)

# Save the best model based on validation loss
checkpoint = ModelCheckpoint(
  "results/trained_models/lstm_model.keras", 
  monitor=MONITOR_METRIC,
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
