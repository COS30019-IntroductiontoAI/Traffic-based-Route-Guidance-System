from __future__ import annotations

from functools import cached_property
import logging

import pandas as pd
import tensorflow as tf

from backend.core.config import ROUTE_GUIDANCE_MONTH, get_default_date, get_default_time_of_day
from src.models.model_loader import (
    PredictionArtifacts,
    SequenceModelArtifacts,
    load_prediction_artifacts,
    load_sequence_model_artifacts,
)

LOGGER = logging.getLogger(__name__)


# Look up prepared model predictions from the shared predictions CSV.
class PredictionInference:
    """Serve route-guidance prediction lookups and sequence model artifacts.

    This class never trains models. It only loads prepared CSV predictions and
    pre-trained .keras artifacts for inference workflows.
    """

    def __init__(self, artifacts: PredictionArtifacts | None = None):
        """Initialize caches for prediction-table and model-artifact access.

        Args:
            artifacts: Optional preloaded prediction table wrapper.
        """
        self.artifacts = artifacts or load_prediction_artifacts()
        self._predictions_cache: dict[str, pd.DataFrame] = {}
        self._route_guidance_cache: dict[str, pd.DataFrame] = {}

    @cached_property
    def default_predictions_df(self) -> pd.DataFrame:
        """Return a cached copy of default prepared prediction rows.

        Returns:
            Prepared predictions dataframe for the default dataset.
        """
        return self.artifacts.predictions.copy()

    @cached_property
    def sequence_models(self) -> SequenceModelArtifacts:
        """Load and cache pre-trained LSTM and GRU models.

        Returns:
            SequenceModelArtifacts containing loaded Keras models.
        """
        LOGGER.info("Loading pre-trained sequence model artifacts for inference")
        return load_sequence_model_artifacts()

    def get_sequence_model(self, model_name: str) -> tf.keras.Model:
        """Return one loaded sequence model by name.

        Args:
            model_name: Model identifier, either "lstm" or "gru".

        Returns:
            Loaded TensorFlow Keras model.

        Raises:
            ValueError: If an unsupported model name is requested.
        """
        normalized = model_name.strip().lower()
        if normalized == "lstm":
            return self.sequence_models.lstm_model
        if normalized == "gru":
            return self.sequence_models.gru_model
        raise ValueError(f"Unsupported sequence model '{model_name}'. Expected 'lstm' or 'gru'.")

    def get_predictions_df(self, data_key: str = "2014") -> pd.DataFrame:
        """Load or reuse prepared prediction rows for a dataset key.

        Args:
            data_key: Dataset identifier (for example, "2014" or "2006").

        Returns:
            Prepared predictions dataframe for the requested dataset.
        """
        normalized = data_key.strip().lower()
        if normalized not in self._predictions_cache:
            if normalized == "2014":
                self._predictions_cache[normalized] = self.default_predictions_df
            else:
                self._predictions_cache[normalized] = load_prediction_artifacts(data_key=normalized).predictions.copy()
        return self._predictions_cache[normalized]

    def get_route_guidance_predictions_df(self, data_key: str = "2014") -> pd.DataFrame:
        """Return prediction rows restricted to the configured routing month.

        Args:
            data_key: Dataset identifier.

        Returns:
            Filtered dataframe for route-guidance calculations.

        Raises:
            ValueError: If no rows exist for the configured routing month.
        """
        normalized = data_key.strip().lower()
        if normalized not in self._route_guidance_cache:
            predictions_df = self.get_predictions_df(normalized)
            month_df = predictions_df[predictions_df["datetime"].dt.month == ROUTE_GUIDANCE_MONTH].copy()
            if month_df.empty:
                raise ValueError(f"No October prediction rows are available for dataset '{data_key}'")
            self._route_guidance_cache[normalized] = month_df
        return self._route_guidance_cache[normalized]

    @cached_property
    def default_site_reference_flows(self) -> dict[str, float]:
        """Return default per-site reference flows for congestion normalization.

        Returns:
            Mapping of SCATS site identifier to reference flow value.
        """
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

    def get_site_reference_flows(self, data_key: str = "2014") -> dict[str, float]:
        """Build site-level reference flows for the requested dataset.

        Args:
            data_key: Dataset identifier.

        Returns:
            Mapping of SCATS site identifier to reference flow value.
        """
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
        """Return available date/time selectors and defaults for route guidance.

        Args:
            data_key: Dataset identifier.

        Returns:
            Dictionary containing available dates, times, and default selections.
        """
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
        """Resolve and validate the requested timestamp for inference lookup.

        Args:
            data_key: Dataset identifier.
            target_datetime: Optional datetime override.

        Returns:
            Validated target timestamp present in prepared data.

        Raises:
            ValueError: If the timestamp is not available.
        """
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

    def predict_site_flow_map(
        self,
        target_datetime: str | None = None,
        prediction_column: str = "predicted_lightgbm",
        data_key: str = "2014",
    ) -> tuple[str, dict[str, float]]:
        """Return predicted flow aggregates per site for a target timestamp.

        Args:
            target_datetime: Optional target timestamp string.
            prediction_column: Prediction column name to aggregate.
            data_key: Dataset identifier.

        Returns:
            Tuple of ISO timestamp and per-site predicted flow mapping.

        Raises:
            ValueError: If required columns or rows are not available.
        """
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
