# Assignment 2 Part B - Traffic-Based Route Guidance System (TBRGS)

## Team Members

| Name | Student ID | Task | Responsibility |
|:---|:---|:---|:---|
| Bui Quang Doan | 104993227 | Task 1 | Data Processing & Dataset Preparation |
| Do Gia Huy | 104988294 | Task 2 | ML Implementation (LSTM/GRU) & Model Evaluation |
| Huynh Doan Hoang Minh | 104777308 | Task 2 | ML Implementation & Model Evaluation |
| Le Thanh Nam | 104999380 | Task 3 & 4 | System Integration, Travel Time Estimation & GUI |

## Project Overview
* **Goal:** Build a Traffic-Based Route Guidance System (TBRGS) for the city of Boroondara.
* **Data:** Use historical SCATS traffic flow data (October 2006) to train machine learning models.
* **Prediction:** Train models such as LSTM, GRU, and XGBoost to predict future traffic flow.
* **Integration:** Convert predicted traffic flow into travel time and use the A* algorithm to find optimal routes.
* **Note:** This repository currently contains Task 1 and initial Task 2 model implementations.

---

## Prerequisites & Installation

### Python Version

This project requires **Python 3.12** or later.

### Install Dependencies

Install all required packages using:

```bash
pip install -r requirements.txt
```

## Task 1: Data Preprocessing

This section covers the `preprocessing_data.py` script, which extracts, cleans, and reshapes the raw VicRoads dataset to prepare it for machine learning training.

### How to Run

Execute the script from the root folder:

```bash
python src/preprocessing_data.py
```

The output will be saved as `processed_traffic.csv` in the `data/processed/` directory.

The processed dataset will be used in later stages for training the machine learning models.

### Processing Steps

The script performs the following operations on the raw dataset:

* Standardizes column names (lowercase, stripped spaces, underscores).
* Reshapes data from wide format (v00-v95 intervals) to a long format time series.
* Converts interval time codes into HH:MM:SS format and creates a unified datetime column.
* Cleans the dataset by removing the pedestrian counting site (4335) and branches with insufficient data (less than 25 days).
* Handles missing traffic volume values using linear interpolation, forward fill, and backward fill.
* Generates time-based features including hour, day of week, and an `is_weekend` indicator.

---

## Task 2: Model Training

This section covers training multiple machine learning models to predict traffic flow patterns using the preprocessed traffic data.

### How to Run

#### LSTM Model

To train the LSTM (Long Short-Term Memory) model, execute:

```bash
python -m models.lstm_model
```

**What it does:**
* Loads and prepares the preprocessed traffic data
* Builds a sequential LSTM model with 2 stacked LSTM layers (64 and 32 units)
* Uses dropout regularization (0.2) to prevent overfitting
* Trains the model with Adam optimizer and mean squared error loss
* Saves the best model based on validation loss to `results/trained_models/lstm_model.keras`
* Saves the LSTM training curve to `results/trained_models/lstm_training_curve.png`

#### GRU Model

To train the GRU (Gated Recurrent Unit) model, execute:

```bash
python -m models.gru_model
```

**What it does:**
* Loads and prepares the preprocessed traffic data
* Builds a sequential GRU model with 2 stacked GRU layers (64 and 32 units)
* Uses dropout regularization (0.2) to prevent overfitting
* Trains the model with Adam optimizer and mean squared error loss
* Saves the best model based on validation loss to `results/trained_models/gru_model.keras`
* Saves the GRU training curve to `results/trained_models/gru_training_curve.png`

#### XGBoost Model

To train the XGBoost baseline model, execute:

```bash
python -m models.xgboost_model
```

To evaluate the saved XGBoost model, execute:

```bash
python src/evaluate_xgboost.py
```

To export XGBoost prediction files, execute:

```bash
python src/predict_xgboost.py
```

**What it does:**
* Loads the preprocessed traffic data from `data/processed/processed_traffic.csv`
* Builds a tabular feature set for XGBoost using time-based features and lag-based history
* Trains an XGBoost regressor to predict traffic flow
* Evaluates performance using MAE, RMSE, and MAPE
* Exports 15-minute and hourly prediction files for downstream integration
* Saves outputs to `results/trained_models/`

### Model Architecture

The current Task 2 models use two different modelling styles:

* **LSTM / GRU:** Sequence models using 96 time intervals (24 hours of 15-minute intervals) to predict the next 15-minute traffic flow value
* **XGBoost:** A tabular regression baseline using time-based and lag-based features derived from the processed traffic data

### Model Outputs

After training and evaluation, the following files are generated:

* `results/trained_models/gru_model.keras` - Trained GRU model
* `results/trained_models/lstm_model.keras` - Trained LSTM model
* `results/trained_models/gru_training_curve.png` - GRU training curve
* `results/trained_models/lstm_training_curve.png` - LSTM training curve
* `results/trained_models/xgboost_model.joblib` - Trained XGBoost model
* `results/trained_models/xgboost_metadata.json` - XGBoost metadata and split configuration
* `results/trained_models/xgboost_metrics.json` - XGBoost evaluation metrics
* `results/trained_models/xgboost_results.csv` - XGBoost 15-minute predictions
* `results/trained_models/xgboost_hourly_results.csv` - XGBoost hourly predictions

### Notes

* The XGBoost baseline currently includes some design assumptions that still need tutor confirmation.
* A detailed list of current assumptions and discussion points is documented in `models/XGBOOST_TUTOR_QUESTIONS.md`.
