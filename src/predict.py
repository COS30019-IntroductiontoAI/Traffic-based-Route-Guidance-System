from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


# ----------------------------------------
# --- Sequence-Based Prediction Helper ---
# ----------------------------------------

# Convert normalized values back to the original traffic scale.
def inverse_transform(scaler, data: np.ndarray) -> np.ndarray:
    flat = data.flatten()
    dummy = np.zeros((len(flat), scaler.n_features_in_))
    dummy[:, 0] = flat
    inversed = scaler.inverse_transform(dummy)[:, 0]
    return np.expm1(inversed)


# Load a saved sequence model and return actual and predicted values on the original scale.
def predict_sequence_model(model_path: str | Path, x_test: np.ndarray, y_test: np.ndarray, scaler):
    from tensorflow.keras.models import load_model

    model = load_model(model_path)
    predictions = model.predict(x_test)

    actual_real = inverse_transform(scaler, y_test)
    predicted_real = inverse_transform(scaler, predictions.flatten())
    return actual_real, predicted_real


# ------------------------------
# --- Tabular Prediction Helper ---
# ------------------------------

# Predict traffic values from a tabular feature frame.
def predict_tabular_model(model, feature_df: pd.DataFrame, feature_columns: list[str]) -> np.ndarray:
    return model.predict(feature_df[feature_columns])
