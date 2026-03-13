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
* **Prediction:** Train models such as LSTM and GRU to predict future traffic flow.
* **Integration:** Convert predicted traffic flow into travel time and use the A* algorithm to find optimal routes.
* **Note:** This repository currently focuses on Task 1 (Data Preprocessing). Other modules will be added later by team members.

---

## Task 1: Data Preprocessing

This section covers the `preprocessing_data.py` script, which extracts, cleans, and reshapes the raw VicRoads dataset to prepare it for machine learning training.

### Prerequisites

Make sure Python is installed. Install the required libraries using:

```bash
pip install pandas openpyxl
```

### How to Run

Execute the script from the root folder:

```bash
python preprocessing_data.py
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

## Task 2: XGBoost Baseline

This section covers the initial XGBoost baseline implementation for Task 2, which is used as the third machine learning model for traffic flow prediction.

### Files

The XGBoost baseline is located in:

* `models/xgboost/model_xgboost.py`
* `models/xgboost/evaluate_xgboost.py`
* `models/xgboost/predict_xgboost.py`

### Prerequisites

Make sure Python is installed. Install the required libraries using:

```bash
pip install pandas numpy scikit-learn xgboost joblib
```

### How to Run

Train the model:

```bash
python models/xgboost/model_xgboost.py
```

Evaluate the saved model:

```bash
python models/xgboost/evaluate_xgboost.py
```

Export prediction files:

```bash
python models/xgboost/predict_xgboost.py
```

The output files will be saved in the `models/xgboost/outputs/` directory.

### Notes

* This implementation is currently an initial baseline for Task 2.
* Some design decisions, including prediction granularity and feature engineering, still need tutor confirmation.

