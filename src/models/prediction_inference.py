from __future__ import annotations

from functools import cached_property

import pandas as pd

from src.models.model_loader import PredictionArtifacts, load_prediction_artifacts


# Look up prepared model predictions from the shared predictions CSV.
class PredictionInference:
    def __init__(self, artifacts: PredictionArtifacts | None = None):
        self.artifacts = artifacts or load_prediction_artifacts()
        self._predictions_cache: dict[str, pd.DataFrame] = {}

    @cached_property
    # Cache the prepared predictions table once for repeated route queries.
    def default_predictions_df(self) -> pd.DataFrame:
        return self.artifacts.predictions.copy()

    # Load or reuse the prepared predictions table for the requested dataset.
    def get_predictions_df(self, data_key: str = "2014") -> pd.DataFrame:
        normalized = data_key.strip().lower()
        if normalized not in self._predictions_cache:
            if normalized == "2014":
                self._predictions_cache[normalized] = self.default_predictions_df
            else:
                self._predictions_cache[normalized] = load_prediction_artifacts(data_key=normalized).predictions.copy()
        return self._predictions_cache[normalized]

    @cached_property
    # Use historical site-level 75th-percentile actual flow as a congestion reference.
    def default_site_reference_flows(self) -> dict[str, float]:
        site_actuals = (
            self.default_predictions_df.groupby(["datetime", "scats_number"], observed=False)["actual"]
            .sum()
            .reset_index()
        )
        references = (
            site_actuals.groupby("scats_number", observed=False)["actual"]
            .quantile(0.75)
            .to_dict()
        )
        return {str(site): float(value) for site, value in references.items()}

    # Build site-level reference flows for the requested dataset.
    def get_site_reference_flows(self, data_key: str = "2014") -> dict[str, float]:
        normalized = data_key.strip().lower()
        if normalized == "2014":
            return self.default_site_reference_flows

        predictions_df = self.get_predictions_df(normalized)
        site_actuals = (
            predictions_df.groupby(["datetime", "scats_number"], observed=False)["actual"]
            .sum()
            .reset_index()
        )
        references = (
            site_actuals.groupby("scats_number", observed=False)["actual"]
            .quantile(0.75)
            .to_dict()
        )
        return {str(site): float(value) for site, value in references.items()}

    # Return one predicted site-level flow value per SCATS site for a target timestamp.
    def predict_site_flow_map(
        self,
        target_datetime: str | None = None,
        prediction_column: str = "predicted_lightgbm",
        data_key: str = "2014",
    ) -> tuple[str, dict[str, float]]:
        feature_df = self.get_predictions_df(data_key)
        if prediction_column not in feature_df.columns:
            raise ValueError(f"Prediction column '{prediction_column}' is missing from the prepared CSV")

        if target_datetime is None:
            target_timestamp = feature_df["datetime"].max()
        else:
            target_timestamp = pd.Timestamp(target_datetime)

        target_rows = feature_df[feature_df["datetime"] == target_timestamp].copy()
        if target_rows.empty:
            raise ValueError(f"No prepared prediction rows found for timestamp {target_datetime}")

        target_rows["predicted_flow"] = target_rows[prediction_column].astype(float)
        site_predictions = (
            target_rows.groupby("scats_number", observed=False)["predicted_flow"]
            .sum()
            .to_dict()
        )
        site_predictions = {str(site): float(value) for site, value in site_predictions.items()}
        return pd.Timestamp(target_timestamp).isoformat(), site_predictions
