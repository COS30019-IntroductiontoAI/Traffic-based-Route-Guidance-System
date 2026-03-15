from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.evaluation import plot_predictions
from src.predict import predict_tabular_model
from models.xgboost_model import (
    FEATURE_COLUMNS,
    OUTPUT_DIR,
    TARGET_COLUMN,
    build_feature_frame,
    load_metadata,
    load_trained_model,
    split_feature_frame,
)


PLOT_OUTPUT_PATH = OUTPUT_DIR / "xgboost_predictions.png"

# Create the actual and predicted arrays for the XGBoost test set.
def build_prediction_arrays() -> tuple[pd.Series, pd.Series]:
    metadata = load_metadata()
    train_end = pd.Timestamp(metadata["train_end"])
    val_end = pd.Timestamp(metadata["val_end"])

    feature_df = build_feature_frame()
    _, _, test_df = split_feature_frame(feature_df, train_end, val_end)

    model = load_trained_model()
    predicted_flow = predict_tabular_model(
        model,
        test_df,
        FEATURE_COLUMNS,
    ).round(2)
    actual_flow = test_df[TARGET_COLUMN].reset_index(drop=True)
    predicted_flow = pd.Series(predicted_flow, name="predicted_flow")
    return actual_flow, predicted_flow

# Run prediction and save a plot in the same flow style used by Huy's models.
def main() -> None:
    print("Generating XGBoost predictions and plot...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    actual_flow, predicted_flow = build_prediction_arrays()

    plot_predictions(
        actual_flow.to_numpy(dtype=float),
        predicted_flow.to_numpy(dtype=float),
        "XGBoost Model Predictions",
        PLOT_OUTPUT_PATH,
    )

    print("Prediction plot saved to:", PLOT_OUTPUT_PATH.name)


if __name__ == "__main__":
    main()
