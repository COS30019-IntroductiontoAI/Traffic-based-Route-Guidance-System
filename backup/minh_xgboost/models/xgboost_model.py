from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
OUTPUT_DIR = PROJECT_ROOT / "results" / "trained_models"
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "processed_traffic.csv"
MODEL_PATH = OUTPUT_DIR / "xgboost_model.joblib"
METADATA_PATH = OUTPUT_DIR / "xgboost_metadata.json"

TARGET_COLUMN = "traffic_volume"
SITE_COLUMN = "scats_number"
MOVEMENT_COLUMN = "location"
TIME_COLUMN = "datetime"
SEQUENCE_LENGTH = 96
FORECAST_HORIZON = 1
BASE_FEATURE_COLUMNS = [
    SITE_COLUMN,
    "movement_code",
    "hour",
    "day_of_week",
    "is_weekend",
]
LAG_FEATURE_COLUMNS = [f"lag_{step}" for step in range(SEQUENCE_LENGTH, 0, -1)]
FEATURE_COLUMNS = BASE_FEATURE_COLUMNS + LAG_FEATURE_COLUMNS


# Load the processed CSV and keep the original movement-level traffic rows.
def load_movement_level_data(data_path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(data_path, parse_dates=[TIME_COLUMN])
    df = df.sort_values([SITE_COLUMN, MOVEMENT_COLUMN, TIME_COLUMN]).reset_index(drop=True)
    df["movement_id"] = df[SITE_COLUMN].astype(str) + " | " + df[MOVEMENT_COLUMN]
    return df


# Convert each movement sequence into a tabular row using the previous 96 values as features.
def build_feature_frame(data_path: Path = DATA_PATH) -> pd.DataFrame:
    movement_df = load_movement_level_data(data_path)
    feature_rows = []

    for (_, _), group_df in movement_df.groupby([SITE_COLUMN, MOVEMENT_COLUMN], sort=False):
        group_df = group_df.sort_values(TIME_COLUMN).reset_index(drop=True)
        traffic_values = group_df[TARGET_COLUMN].to_numpy(dtype=float)

        # Each training row is created from one rolling sequence window.
        for start_idx in range(len(group_df) - SEQUENCE_LENGTH - FORECAST_HORIZON + 1):
            history_window = traffic_values[start_idx : start_idx + SEQUENCE_LENGTH]
            target_idx = start_idx + SEQUENCE_LENGTH + FORECAST_HORIZON - 1
            target_row = group_df.iloc[target_idx]

            row = {
                SITE_COLUMN: int(target_row[SITE_COLUMN]),
                MOVEMENT_COLUMN: target_row[MOVEMENT_COLUMN],
                "movement_id": target_row["movement_id"],
                TIME_COLUMN: target_row[TIME_COLUMN],
                "hour": int(target_row["hour"]),
                "day_of_week": int(target_row["day_of_week"]),
                "is_weekend": int(target_row["is_weekend"]),
                TARGET_COLUMN: float(target_row[TARGET_COLUMN]),
            }

            # Flatten the sequence so XGBoost can consume it as tabular input.
            for lag_step, lag_value in zip(range(SEQUENCE_LENGTH, 0, -1), history_window):
                row[f"lag_{lag_step}"] = float(lag_value)

            feature_rows.append(row)

    feature_df = pd.DataFrame(feature_rows)
    feature_df["movement_code"] = feature_df["movement_id"].astype("category").cat.codes
    return feature_df


# Compute chronological split boundaries using the target timestamp of each training row.
def get_split_boundaries(
    feature_df: pd.DataFrame,
    train_ratio: float = 0.7,
    val_ratio: float = 0.1,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    unique_times = feature_df[TIME_COLUMN].sort_values().drop_duplicates().reset_index(drop=True)
    train_end_idx = int(len(unique_times) * train_ratio) - 1
    val_end_idx = int(len(unique_times) * (train_ratio + val_ratio)) - 1

    train_end_idx = max(train_end_idx, 0)
    val_end_idx = min(max(val_end_idx, train_end_idx + 1), len(unique_times) - 1)

    train_end = unique_times.iloc[train_end_idx]
    val_end = unique_times.iloc[val_end_idx]
    return train_end, val_end


# Split the movement-level feature frame into train, validation, and test sets by time order.
def split_feature_frame(
    feature_df: pd.DataFrame,
    train_end: pd.Timestamp,
    val_end: pd.Timestamp,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_df = feature_df[feature_df[TIME_COLUMN] <= train_end].copy()
    val_df = feature_df[
        (feature_df[TIME_COLUMN] > train_end) & (feature_df[TIME_COLUMN] <= val_end)
    ].copy()
    test_df = feature_df[feature_df[TIME_COLUMN] > val_end].copy()
    return train_df, val_df, test_df


# Return model inputs X and target y from a prepared dataframe.
def get_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    return df[FEATURE_COLUMNS], df[TARGET_COLUMN]


# Calculate MAE, RMSE, and MAPE for regression evaluation.
def calculate_metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    non_zero_mask = y_true != 0
    if np.any(non_zero_mask):
        mape = float(
            np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask]))
            * 100
        )
    else:
        mape = 0.0

    return {"mae": mae, "rmse": rmse, "mape": mape}


# Build the XGBoost regressor with a simple baseline configuration.
def create_model() -> XGBRegressor:
    return XGBRegressor(
        objective="reg:squarederror",
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=4,
    )


# Store the split settings and feature layout so evaluation uses the same configuration.
def save_metadata(train_end: pd.Timestamp, val_end: pd.Timestamp, row_count: int) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metadata = {
        "data_path": str(DATA_PATH),
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "site_column": SITE_COLUMN,
        "movement_column": MOVEMENT_COLUMN,
        "time_column": TIME_COLUMN,
        "sequence_length": SEQUENCE_LENGTH,
        "forecast_horizon": FORECAST_HORIZON,
        "train_end": train_end.isoformat(),
        "val_end": val_end.isoformat(),
        "row_count_after_features": row_count,
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


# Load the saved training metadata from disk.
def load_metadata() -> dict:
    return json.loads(METADATA_PATH.read_text(encoding="utf-8"))


# Load the trained XGBoost model from disk.
def load_trained_model() -> XGBRegressor:
    return joblib.load(MODEL_PATH)


# Train the movement-level XGBoost model and save the resulting artifacts.
def train_xgboost_model() -> tuple[XGBRegressor, dict[str, dict[str, float]]]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    feature_df = build_feature_frame()
    train_end, val_end = get_split_boundaries(feature_df)
    train_df, val_df, test_df = split_feature_frame(feature_df, train_end, val_end)

    x_train, y_train = get_xy(train_df)
    x_val, y_val = get_xy(val_df)
    x_test, y_test = get_xy(test_df)

    model = create_model()
    model.fit(x_train, y_train)

    val_metrics = calculate_metrics(y_val, model.predict(x_val))
    test_metrics = calculate_metrics(y_test, model.predict(x_test))

    joblib.dump(model, MODEL_PATH)
    save_metadata(train_end, val_end, len(feature_df))

    metrics = {"validation": val_metrics, "test": test_metrics}
    return model, metrics


# Run the end-to-end training script from the command line.
def main() -> None:
    print("Training XGBoost model for movement-level traffic prediction...")
    _, metrics = train_xgboost_model()
    print("Training completed.")
    print("Validation metrics:", metrics["validation"])
    print("Test metrics:", metrics["test"])
    print("Model saved to:", MODEL_PATH.name)
    print("Metadata saved to:", METADATA_PATH.name)


if __name__ == "__main__":
    main()
