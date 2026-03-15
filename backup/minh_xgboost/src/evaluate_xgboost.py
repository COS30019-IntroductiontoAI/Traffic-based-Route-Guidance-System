from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.evaluation import evaluate_tabular_predictions
from models.xgboost_model import (
    OUTPUT_DIR,
    build_feature_frame,
    get_xy,
    load_metadata,
    load_trained_model,
    split_feature_frame,
)


METRICS_OUTPUT_PATH = OUTPUT_DIR / "xgboost_metrics.json"

# Rebuild the test split from saved metadata and score the saved model.
def evaluate_model() -> dict:
    metadata = load_metadata()
    train_end = pd.Timestamp(metadata["train_end"])
    val_end = pd.Timestamp(metadata["val_end"])

    feature_df = build_feature_frame()
    train_df, val_df, test_df = split_feature_frame(feature_df, train_end, val_end)

    model = load_trained_model()

    # We regenerate the same splits instead of saving raw split files to keep the workflow simple.
    _, y_val = get_xy(val_df)
    x_val, _ = get_xy(val_df)
    _, y_test = get_xy(test_df)
    x_test, _ = get_xy(test_df)

    results = {
        "validation": evaluate_tabular_predictions(y_val.to_numpy(dtype=float), model.predict(x_val)),
        "test": evaluate_tabular_predictions(y_test.to_numpy(dtype=float), model.predict(x_test)),
    }
    return results

# Run evaluation and export the metrics JSON file.
def main() -> None:
    print("Evaluating saved XGBoost model...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics = evaluate_model()
    METRICS_OUTPUT_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print("Validation metrics:", metrics["validation"])
    print("Test metrics:", metrics["test"])
    print("Metrics saved to:", METRICS_OUTPUT_PATH.name)


if __name__ == "__main__":
    main()
