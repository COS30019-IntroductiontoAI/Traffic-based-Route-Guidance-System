import numpy as np
import matplotlib.pyplot as plt 
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from src.data_loader import prepare_data


# ------------------------------------
# --- 1. LOAD AND PREPARE THE DATA ---
# ------------------------------------
(X_train, y_train), (X_val, y_val), (X_test, y_test), scaler = prepare_data(
  "data/processed/processed_traffic.csv",
  seq_len=192,            # Using past 48 hours of data (192 intervals of 15 minutes)
  forecast_horizon=1      # Predicting the next 15 minutes (1 interval ahead)
)


# -------------------------------
# --- 2. BUILD THE LSTM MODEL ---
# -------------------------------
model = Sequential([
  LSTM(units=128, return_sequences=True, input_shape=(192, 4)),
  Dropout(0.3),
  LSTM(units=64, return_sequences=False),
  Dropout(0.3),
  Dense(units=1)
])

# Compile the model with Adam optimizer and mean squared error loss function
model.compile(optimizer=Adam(learning_rate=0.0005), loss="mse")
model.summary()


# --------------------
# --- 3. CALLBACKS ---
# --------------------
early_stop = EarlyStopping(
  monitor="val_loss",
  patience=10,
  restore_best_weights=True
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
  epochs=100,
  batch_size=1024,
  callbacks=[early_stop, checkpoint]
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