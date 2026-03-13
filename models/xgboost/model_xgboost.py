from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[1]
OUTPUT_DIR = BASE_DIR / "outputs"
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "processed_traffic.csv"
MODEL_PATH = OUTPUT_DIR / "xgboost_model.joblib"
METADATA_PATH = OUTPUT_DIR / "xgboost_metadata.json"

TARGET_COLUMN = "traffic_volume"
SITE_COLUMN = "scats_number"
TIME_COLUMN = "datetime"
FEATURE_COLUMNS = [
    "hour",
    "day_of_week",
    "is_weekend",
    "lag_1",
    "lag_2",
    "lag_4",
    "lag_8",
    "lag_96",
    "rolling_mean_4",
    "rolling_mean_8",
]

# Load the processed CSV and aggregate traffic flow to one row per site and timestamp.
def load_site_level_data(data_path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(data_path, parse_dates=[TIME_COLUMN])

    site_df = (
        # The original processed file contains multiple movements per SCATS site.
        # For this model we collapse them into a single site-level traffic flow.
        df.groupby([SITE_COLUMN, TIME_COLUMN], as_index=False)[TARGET_COLUMN]
        .sum()
        .sort_values([SITE_COLUMN, TIME_COLUMN])
        .reset_index(drop=True)
    )

    # These calendar features are lightweight signals that tree models can learn from easily.
    site_df["hour"] = site_df[TIME_COLUMN].dt.hour
    site_df["day_of_week"] = site_df[TIME_COLUMN].dt.dayofweek
    site_df["is_weekend"] = (site_df["day_of_week"] >= 5).astype(int)
    return site_df

# Create lag-based features for each site and drop rows that do not have enough history.
def build_feature_frame(data_path: Path = DATA_PATH) -> pd.DataFrame:
    site_df = load_site_level_data(data_path)
    grouped = site_df.groupby(SITE_COLUMN)[TARGET_COLUMN]

    # Lags let the model look at recent traffic history:
    # lag_1 = previous 15 minutes, lag_4 = previous hour, lag_96 = previous day.
    site_df["lag_1"] = grouped.shift(1)
    site_df["lag_2"] = grouped.shift(2)
    site_df["lag_4"] = grouped.shift(4)
    site_df["lag_8"] = grouped.shift(8)
    site_df["lag_96"] = grouped.shift(96)

    # shift(1) prevents the rolling window from leaking the current target value.
    site_df["rolling_mean_4"] = grouped.transform(lambda s: s.shift(1).rolling(window=4).mean())
    site_df["rolling_mean_8"] = grouped.transform(lambda s: s.shift(1).rolling(window=8).mean())

    # Early rows per site will contain NaN because they do not have enough previous history yet.
    feature_df = site_df.dropna().reset_index(drop=True)
    return feature_df

# Compute chronological split boundaries for train and validation.
def get_split_boundaries(
    feature_df: pd.DataFrame,
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    unique_times = feature_df[TIME_COLUMN].sort_values().drop_duplicates().reset_index(drop=True)
    train_end_idx = int(len(unique_times) * train_ratio) - 1
    val_end_idx = int(len(unique_times) * (train_ratio + val_ratio)) - 1

    # Guard rails keep the split valid even on smaller datasets.
    train_end_idx = max(train_end_idx, 0)
    val_end_idx = min(max(val_end_idx, train_end_idx + 1), len(unique_times) - 1)

    train_end = unique_times.iloc[train_end_idx]
    val_end = unique_times.iloc[val_end_idx]
    return train_end, val_end

# Split the feature frame into train, validation, and test sets by time order.
def split_feature_frame(
    feature_df: pd.DataFrame,
    train_end: pd.Timestamp,
    val_end: pd.Timestamp,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # We split by timestamp instead of random shuffle because this is time-series data.
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

    # MAPE is undefined when the true value is zero, so those rows are skipped.
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

# Store split boundaries and feature settings so evaluation uses the same setup.
def save_metadata(train_end: pd.Timestamp, val_end: pd.Timestamp, row_count: int) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metadata = {
        "data_path": str(DATA_PATH),
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "site_column": SITE_COLUMN,
        "time_column": TIME_COLUMN,
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

# Train the model, evaluate it on validation/test sets, and save artifacts.
def train_xgboost_model() -> tuple[XGBRegressor, dict[str, dict[str, float]]]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    feature_df = build_feature_frame()
    train_end, val_end = get_split_boundaries(feature_df)
    train_df, val_df, test_df = split_feature_frame(feature_df, train_end, val_end)

    x_train, y_train = get_xy(train_df)
    x_val, y_val = get_xy(val_df)
    x_test, y_test = get_xy(test_df)

    # This baseline trains directly on tabular lag features without extra scaling.
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
    print("Training XGBoost model for site-level traffic prediction...")
    _, metrics = train_xgboost_model()
    print("Training completed.")
    print("Validation metrics:", metrics["validation"])
    print("Test metrics:", metrics["test"])
    print("Model saved to:", MODEL_PATH.name)
    print("Metadata saved to:", METADATA_PATH.name)


if __name__ == "__main__":
    main()
