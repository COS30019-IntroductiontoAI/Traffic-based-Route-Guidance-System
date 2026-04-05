from __future__ import annotations

from pathlib import Path

import pandas as pd

from backend.core.config import get_predictions_path


# Hold one prepared predictions table so backend services can share it safely.
class PredictionArtifacts:
    # Keep the CSV-backed prediction frame in one small container object.
    def __init__(self, predictions: pd.DataFrame):
        self.predictions = predictions


# Load one prepared predictions CSV for route guidance lookup.
def load_prediction_artifacts(
    predictions_path: str | Path | None = None,
    data_key: str = "2014",
) -> PredictionArtifacts:
    # The backend should reuse prepared CSV outputs instead of rerunning models at request time.
    if predictions_path is None:
        predictions_path = get_predictions_path(data_key)
    
    # Validate the file exists with clear error message
    predictions_path = Path(predictions_path)
    if not predictions_path.exists():
        raise FileNotFoundError(
            f"Predictions CSV file not found for dataset '{data_key}' at {predictions_path}. "
            f"Please ensure the predictions file exists or run the prediction pipeline first."
        )

    try:
        predictions = pd.read_csv(predictions_path, parse_dates=["datetime"])
    except Exception as e:
        raise ValueError(f"Failed to load predictions from {predictions_path}: {e}") from e

    # Sorting once here keeps downstream timestamp and grouping logic deterministic.
    # The route layer depends on stable ordering when it builds date/time selectors and site-level aggregates.
    predictions = predictions.sort_values(["datetime", "scats_number", "location"]).reset_index(drop=True)
    return PredictionArtifacts(predictions=predictions)
