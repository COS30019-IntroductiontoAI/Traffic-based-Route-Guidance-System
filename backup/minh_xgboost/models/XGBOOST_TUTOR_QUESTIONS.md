# XGBoost Task 2 Implementation Notes

## Purpose of This Document

This document summarises the final implementation decisions currently used for the XGBoost baseline in Task 2.

These notes are no longer written as open tutor questions. The team has already agreed on the overall direction for the XGBoost model, and this file now serves as a short design reference for implementation and report writing.

---

## Why XGBoost Was Chosen

The assignment requires at least three machine learning models, including:

- LSTM
- GRU
- one additional model chosen by the team

XGBoost was selected as the third model because:

- it works well on structured tabular data
- it is faster to train and debug than another deep learning model
- it gives the team a useful non-sequence baseline to compare against LSTM and GRU
- it is still flexible enough to model time-series behaviour when the sequence history is converted into tabular features

---

## Prediction Level

The team decided to use **movement-level prediction** for the XGBoost baseline.

This means the model predicts traffic flow for each:

- `scats_number`
- `location`
- `datetime`

The data is **not** aggregated into site-level totals.

This keeps the XGBoost target aligned with the granularity already present in the processed dataset.

---

## How Sequence Data Is Used in XGBoost

LSTM and GRU consume input as ordered sequences.

XGBoost does not work that way. It expects a tabular dataset where:

- each row is one training example
- each column is one feature

To make XGBoost compatible with the same traffic history idea, the model uses a **sequence-derived tabular representation**.

For each movement-level series, a sliding window is built from the previous 96 traffic values:

- `lag_96`
- `lag_95`
- ...
- `lag_2`
- `lag_1`

These 96 lag columns represent the past 24 hours of 15-minute traffic intervals.

So the sequence is still being used, but it is flattened into a table before training.

---

## Features Used by the Current XGBoost Baseline

The current XGBoost input includes:

- `scats_number`
- `movement_code`
- `hour`
- `day_of_week`
- `is_weekend`
- `lag_96` to `lag_1`

### Why these features are used

- `scats_number` helps identify the intersection
- `movement_code` helps distinguish different directions or approaches at the same site
- `hour`, `day_of_week`, and `is_weekend` capture basic calendar patterns
- `lag_96` to `lag_1` capture the recent traffic history in a form XGBoost can use

This design lets XGBoost learn from the same time history idea as sequence models, but in tabular form.

---

## Train / Validation / Test Split

The current XGBoost baseline uses a chronological split:

- 70% training
- 10% validation
- 20% testing

This follows the same spirit as the sequence-based workflow and avoids leaking future observations into training.

The split is based on the target timestamp of each movement-level training row.

---

## Output Format

The team decided to keep the XGBoost output at the original **15-minute level** only.

The current prediction flow follows the same high-level style as the sequence models:

- generate predictions on the test set
- evaluate the predictions
- save a prediction plot for visual comparison

No hourly aggregation is generated in the current version.

---

## Files Used in the Current XGBoost Baseline

- `models/xgboost_model.py`
- `src/evaluate_xgboost.py`
- `src/predict_xgboost.py`
- `results/trained_models/xgboost_model.joblib`
- `results/trained_models/xgboost_metadata.json`
- `results/trained_models/xgboost_metrics.json`
- `results/trained_models/xgboost_predictions.png`

---

## Summary

The current XGBoost baseline is based on these final implementation choices:

- movement-level prediction
- sequence history flattened into tabular lag features
- chronological train / validation / test split
- 15-minute output only

This keeps the model aligned with the processed dataset while still fitting the XGBoost training style.
