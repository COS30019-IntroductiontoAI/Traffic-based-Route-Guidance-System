# XGBoost Task 2 Notes and Questions for Tutor

## Purpose of This Document

This document summarises the current XGBoost baseline implementation for Task 2 and highlights the design decisions that still need tutor confirmation.

The goal is not to claim that these decisions are final. Instead, this note is intended to help the team ask clear questions before continuing with more implementation and report writing.

---

## Why XGBoost Was Chosen for Task 2

The assignment requires at least three machine learning models, including:

- LSTM
- GRU
- one additional model chosen by the team

For the third model, XGBoost was selected as an initial baseline for the following reasons:

- It is strong on structured tabular data
- It is faster to train and debug than another deep learning model
- It is easier to evaluate and explain in a report
- It provides a useful contrast against sequence-based models such as LSTM and GRU

This choice was made as a practical engineering decision for the current implementation.

However, the assignment does not explicitly require XGBoost. It is only one possible choice for the third model, so the team should still confirm that this is an acceptable direction.

---

## Current Scope of the XGBoost Baseline

The current XGBoost implementation is located in:

- `models/xgboost/model_xgboost.py`
- `models/xgboost/evaluate_xgboost.py`
- `models/xgboost/predict_xgboost.py`

At the moment, this baseline does the following:

- Reads the processed traffic dataset from `data/processed/processed_traffic.csv`
- Builds a tabular regression dataset for XGBoost
- Trains an XGBoost regressor to predict traffic flow
- Evaluates the model using MAE, RMSE, and MAPE
- Exports both 15-minute predictions and hourly aggregated predictions

This gives the team a working third model for Assignment 2 Part B, alongside the required LSTM and GRU models.

---

## Important Design Decision 1: Prediction Granularity

### What the processed dataset looks like

The processed dataset still contains multiple `location` or movement rows for the same `scats_number` at the same timestamp.

This means the data can be interpreted at two different levels:

- **Movement-level**
  Each row represents traffic for one direction or approach of a SCATS site.

- **Site-level**
  All movements at the same SCATS site and timestamp are combined into one total traffic flow value.

### What the current XGBoost baseline does

The current implementation aggregates rows by:

- `scats_number`
- `datetime`

and sums `traffic_volume`.

This converts the data from movement-level to site-level.

### Why this was done

This was chosen for practical reasons:

- It simplifies the regression problem
- It reduces the number of target series
- It makes the output easier to connect with route guidance later, because SCATS sites are closer to graph nodes than movement rows are

### Why this needs tutor confirmation

The assignment specification requires traffic prediction, but it does not clearly state whether prediction should be performed at:

- movement-level, or
- site-level

So this aggregation choice is an implementation assumption, not a confirmed assignment requirement.

### Question for tutor

Is it acceptable for the XGBoost baseline to predict **site-level aggregated traffic flow** instead of **movement-level traffic flow**?

If movement-level prediction is expected, the current baseline will need to be redesigned so that each `(scats_number, location)` series is modelled separately.

---

## Important Design Decision 2: Feature Engineering

### Why feature engineering is needed

XGBoost is a tree-based model, not a sequence model like LSTM or GRU.

Unlike recurrent neural networks, XGBoost does not automatically learn temporal memory from the order of observations. Because of that, time-series information must be expressed explicitly as input features.

In other words, the model does not directly consume a raw traffic sequence the way an LSTM or GRU does. Instead, the sequence must first be converted into a tabular format, where each row is one training example and each column is one feature.

This is why feature engineering is a central part of the XGBoost baseline.

### What features are currently used

The current XGBoost baseline uses:

- `hour`
- `day_of_week`
- `is_weekend`
- `lag_1`
- `lag_2`
- `lag_4`
- `lag_8`
- `lag_96`
- `rolling_mean_4`
- `rolling_mean_8`

### What these features mean

- `lag_1`: traffic flow from the previous 15-minute interval
- `lag_2`: traffic flow from 30 minutes earlier
- `lag_4`: traffic flow from 1 hour earlier
- `lag_8`: traffic flow from 2 hours earlier
- `lag_96`: traffic flow from the same time on the previous day
- `rolling_mean_4`: average traffic flow over the previous 1 hour
- `rolling_mean_8`: average traffic flow over the previous 2 hours

### Why this needs tutor confirmation

These features are reasonable for a baseline, but they are still hand-crafted assumptions.

There are still open questions such as:

- Should the model use only recent history, or also include stronger daily patterns?
- Should more calendar features be added, such as day-of-month or holiday indicators?
- Should site identity be encoded explicitly as a model feature?
- Should movement-level features be preserved if the tutor wants movement-based prediction?

### Question for tutor

Is the current feature engineering approach acceptable for the third model baseline, or should the team preserve a more fine-grained representation of the original processed data?

---

## Important Design Decision 3: Time-Series Splitting Strategy

### What the current XGBoost baseline does

The implementation splits data chronologically into:

- training set
- validation set
- test set

This is done using time order instead of random shuffling.

### Why this was done

This is standard practice for time-series prediction.

If random shuffle is used, future observations can leak into the training process, which makes evaluation unrealistic.

### Why this is probably safe

This decision is strongly aligned with time-series modelling practice, so it is less risky than the previous two decisions.

However, the exact split ratio is still a team choice rather than a fixed assignment rule.

### Question for tutor

Is a chronological train/validation/test split acceptable for all models in the project so that the comparison across XGBoost, LSTM, and GRU remains fair?

---

## Important Design Decision 4: Export Format for Integration

### What the current XGBoost baseline exports

The implementation exports:

- 15-minute predictions
- hourly aggregated predictions

### Why both outputs are useful

- The 15-minute output is closer to the original dataset and is useful for model evaluation
- The hourly output is easier to use when converting traffic flow into speed and travel time later

### Why this needs confirmation

The assignment discusses traffic flow to travel time conversion, but it does not prescribe one exact output format for intermediate model predictions.

So this is again a practical integration choice.

### Question for tutor

Should the ML models output predictions at:

- 15-minute level only,
- hourly level only, or
- both levels for evaluation and integration?

---

## Risks If These Decisions Are Wrong

If the tutor expects movement-level modelling but the team continues with site-level aggregation, then:

- the model target will not match the expected problem formulation
- the evaluation may not be comparable to other team implementations
- integration assumptions may need to be changed later

If the tutor expects a different feature design, then:

- the XGBoost baseline may still work technically
- but it may not align well with the intended interpretation of the data

---

## Recommended Questions to Ask in Class

The team can ask the tutor the following questions directly:

1. For Assignment 2 Part B, is traffic prediction expected at movement-level or site-level?
2. Is it acceptable to aggregate all `location` rows of the same SCATS site into one site-level traffic flow series for the third model baseline?
3. Is a feature-engineered XGBoost baseline with lag and rolling statistics acceptable as the third required model?
4. Should all models produce 15-minute outputs, hourly outputs, or both?
5. Should all team models use the same chronological train/validation/test split for fair comparison?

---

## Current Recommendation

Until the tutor gives a clearer direction, the current XGBoost implementation should be treated as:

- a valid working baseline,
- a practical engineering assumption,
- and a draft solution that may still need adjustment depending on tutor feedback.
