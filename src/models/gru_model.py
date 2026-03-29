import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import GRU, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras import regularizers
from src.data_loader import prepare_data
from src.config.model_config import (
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

SRC_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_2006_PATH = SRC_ROOT / "data" / "processed" / "2006_processed.csv"
TRAINED_MODELS_DIR = SRC_ROOT / "results" / "trained_models"


# ------------------------------------
# --- 1. LOAD AND PREPARE THE DATA ---
# ------------------------------------
(X_train, y_train), (X_val, y_val), (X_test, y_test), scaler, label_encoder = prepare_data(
  str(PROCESSED_2006_PATH),
  seq_len=SEQ_LEN,
  forecast_horizon=FORECAST_HORIZON
)

  
# ------------------------------
# --- 2. BUILD THE GRU MODEL ---
# ------------------------------
model = Sequential([
  GRU(
    units=128,
    return_sequences=True,
    input_shape=(SEQ_LEN, INPUT_FEATURES),
    kernel_regularizer=regularizers.l2(L2_REG),
    recurrent_regularizer=regularizers.l2(L2_REG),
  ),
  Dropout(DROPOUT_RATE),
  GRU(
    units=64,
    return_sequences=True,
    kernel_regularizer=regularizers.l2(L2_REG),
    recurrent_regularizer=regularizers.l2(L2_REG),
  ),
  Dropout(DROPOUT_RATE),
  GRU(
    units=32,
    return_sequences=False,
    kernel_regularizer=regularizers.l2(L2_REG),
    recurrent_regularizer=regularizers.l2(L2_REG),
  ),
  Dense(units=32, activation="relu", kernel_regularizer=regularizers.l2(L2_REG)),
  Dense(units=1)
])

optimizer = Adam(learning_rate=LEARNING_RATE)
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
  str(TRAINED_MODELS_DIR / "gru_model.keras"),
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


# --------------------------------
# --- 5. PLOT TRAINING HISTORY ---
# --------------------------------
plt.figure(figsize=(12, 6))
plt.plot(history.history["loss"], label="Training Loss")
plt.plot(history.history["val_loss"], label="Validation Loss")
plt.title("GRU Model Training and Validation Loss")
plt.xlabel("Epochs")
plt.ylabel("Loss")
plt.legend()
TRAINED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
plt.savefig(TRAINED_MODELS_DIR / "gru_training_curve.png")
plt.show()
