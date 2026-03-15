from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from models.xgboost_model import (
    FEATURE_COLUMNS,
    OUTPUT_DIR,
    SITE_COLUMN,
    TARGET_COLUMN,
    TIME_COLUMN,
    build_feature_frame,
    load_metadata,
    load_trained_model,
    split_feature_frame,
)


PREDICTION_OUTPUT_PATH = OUTPUT_DIR / "xgboost_results.csv"
HOURLY_PREDICTION_OUTPUT_PATH = OUTPUT_DIR / "xgboost_hourly_results.csv"

# Create 15-minute and hourly prediction tables from the saved model.
def build_prediction_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    metadata = load_metadata()
    train_end = pd.Timestamp(metadata["train_end"])
    val_end = pd.Timestamp(metadata["val_end"])

    feature_df = build_feature_frame()
    _, _, test_df = split_feature_frame(feature_df, train_end, val_end)

    model = load_trained_model()

    # Keep the prediction output compact and integration-friendly:
    # one row per site and 15-minute timestamp in the test set.
    prediction_df = test_df[[SITE_COLUMN, TIME_COLUMN, TARGET_COLUMN]].copy()
    prediction_df["predicted_flow"] = model.predict(test_df[FEATURE_COLUMNS]).round(2)
    prediction_df["model_name"] = "XGBoost"
    prediction_df = prediction_df.rename(columns={TARGET_COLUMN: "actual_flow"})
    prediction_df = prediction_df[
        ["model_name", SITE_COLUMN, TIME_COLUMN, "actual_flow", "predicted_flow"]
    ]

    hourly_df = prediction_df.copy()
    # Four 15-minute rows are summed into one hourly flow, which is easier to use for travel-time logic.
    hourly_df["hour_datetime"] = pd.to_datetime(hourly_df[TIME_COLUMN]).dt.floor("h")
    hourly_df = (
        hourly_df.groupby(["model_name", SITE_COLUMN, "hour_datetime"], as_index=False)[
            ["actual_flow", "predicted_flow"]
        ]
        .sum()
        .rename(
            columns={
                "actual_flow": "actual_flow_hourly",
                "predicted_flow": "predicted_flow_hourly",
            }
        )
    )

    return prediction_df, hourly_df

# Run prediction export and save both 15-minute and hourly CSV files.
def main() -> None:
    print("Generating prediction files from saved XGBoost model...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    prediction_df, hourly_df = build_prediction_frames()

    prediction_df.to_csv(PREDICTION_OUTPUT_PATH, index=False)
    hourly_df.to_csv(HOURLY_PREDICTION_OUTPUT_PATH, index=False)

    print("15-minute predictions saved to:", PREDICTION_OUTPUT_PATH.name)
    print("Hourly predictions saved to:", HOURLY_PREDICTION_OUTPUT_PATH.name)


if __name__ == "__main__":
    main()
