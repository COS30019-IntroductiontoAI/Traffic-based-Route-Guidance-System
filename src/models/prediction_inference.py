from __future__ import annotations

from functools import cached_property

import pandas as pd

from backend.core.config import ROUTE_GUIDANCE_MONTH, get_default_date, get_default_time_of_day
from src.models.model_loader import PredictionArtifacts, load_prediction_artifacts


# Look up prepared model predictions from the shared predictions CSV.
class PredictionInference:
    def __init__(self, artifacts: PredictionArtifacts | None = None):
        self.artifacts = artifacts or load_prediction_artifacts()
        self._predictions_cache: dict[str, pd.DataFrame] = {}
        self._route_guidance_cache: dict[str, pd.DataFrame] = {}

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

    def get_route_guidance_predictions_df(self, data_key: str = "2014") -> pd.DataFrame:
        normalized = data_key.strip().lower()
        if normalized not in self._route_guidance_cache:
            predictions_df = self.get_predictions_df(normalized)
            month_df = predictions_df[predictions_df["datetime"].dt.month == ROUTE_GUIDANCE_MONTH].copy()
            if month_df.empty:
                raise ValueError(f"No October prediction rows are available for dataset '{data_key}'")
            self._route_guidance_cache[normalized] = month_df
        return self._route_guidance_cache[normalized]

    @cached_property
    # Use historical site-level 75th-percentile actual flow as a congestion reference.
    def default_site_reference_flows(self) -> dict[str, float]:
        site_actuals = (
            self.get_route_guidance_predictions_df("2014").groupby(["datetime", "scats_number"], observed=False)["actual"]
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

        predictions_df = self.get_route_guidance_predictions_df(normalized)
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

    def get_time_options(self, data_key: str = "2014") -> dict[str, object]:
        predictions_df = self.get_route_guidance_predictions_df(data_key)
        unique_timestamps = predictions_df["datetime"].drop_duplicates().sort_values()
        unique_dates = unique_timestamps.dt.strftime("%Y-%m-%d").drop_duplicates().tolist()
        unique_times = unique_timestamps.dt.strftime("%H:%M").drop_duplicates().sort_values().tolist()

        default_date = get_default_date(data_key)
        if default_date not in unique_dates:
            default_date = unique_dates[0]

        default_time = get_default_time_of_day()
        if default_time not in unique_times:
            default_time = unique_times[0]

        return {
            "data": data_key.strip().lower(),
            "available_dates": [str(date_value) for date_value in unique_dates],
            "min_date": str(unique_dates[0]),
            "max_date": str(unique_dates[-1]),
            "times": [str(time_of_day) for time_of_day in unique_times],
            "default_date": default_date,
            "default_time": default_time,
        }

    def resolve_target_timestamp(self, data_key: str = "2014", target_datetime: str | None = None) -> pd.Timestamp:
        feature_df = self.get_route_guidance_predictions_df(data_key)
        if target_datetime is not None:
            target_timestamp = pd.Timestamp(target_datetime)
        else:
            default_date = get_default_date(data_key)
            default_time = get_default_time_of_day()
            target_timestamp = pd.Timestamp(f"{default_date}T{default_time}:00")

        if target_timestamp not in set(feature_df["datetime"]):
            raise ValueError(f"No prepared prediction rows found for timestamp {target_timestamp.isoformat()}")

        return target_timestamp

    # Return one predicted site-level flow value per SCATS site for a target timestamp.
    def predict_site_flow_map(
        self,
        target_datetime: str | None = None,
        prediction_column: str = "predicted_lightgbm",
        data_key: str = "2014",
    ) -> tuple[str, dict[str, float]]:
        feature_df = self.get_route_guidance_predictions_df(data_key)
        if prediction_column not in feature_df.columns:
            raise ValueError(f"Prediction column '{prediction_column}' is missing from the prepared CSV")

        target_timestamp = self.resolve_target_timestamp(data_key=data_key, target_datetime=target_datetime)

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
