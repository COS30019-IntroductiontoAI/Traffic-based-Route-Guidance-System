# Traffic-Based Route Guidance System (TBRGS)

## Team Members

The initial role for each member in the project

| Name | Student ID | Task | Responsibility |
|:---|:---|:---|:---|
| Bui Quang Doan | 104993227 | Task 1 | Data Processing & Dataset Preparation |
| Do Gia Huy (Leader) | 104988294 | Task 2 | ML Implementation (LSTM/GRU) & Model Evaluation |
| Huynh Doan Hoang Minh | 104777308 | Task 2 | ML Implementation & Model Evaluation |
| Le Thanh Nam | 104999380 | Task 3 & 4 | System Integration, Travel Time Estimation & GUI |

## Project Overview
* **Goal:** Build a Traffic-Based Route Guidance System (TBRGS) for the city of Boroondara.
* **Data:** Use historical SCATS traffic flow data (October 2006) to train machine learning models.
* **Prediction:** Train models such as LSTM and GRU to predict future traffic flow.
* **Integration:** Convert predicted traffic flow into travel time and use the A* algorithm to find optimal routes.
* **Note:** This repository currently focuses on Task 1 (Data Preprocessing). Other modules will be added later by team members.

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

This section covers the `process_2006.py` script, which extracts, cleans, and reshapes the raw VicRoads dataset to prepare it for machine learning training.

### How to Run

Execute the script from the root folder:

```bash
python process_2006.py
```

The output will be saved as `2006_processed.csv` in the `data/processed/` directory.

The processed dataset will be used in later stages for training the machine learning models.

### Processing Steps

The script performs the following operations on the raw dataset:

* Standardizes column names (lowercase, stripped spaces, underscores).
* Reshapes data from wide format (v00–v95 intervals) to a long format time series.
* Converts interval time codes into HH:MM:SS format and creates a unified datetime column.
* Cleans the dataset by removing the pedestrian counting site (4335) and branches with insufficient data (less than 25 days).
* Handles missing traffic volume values using linear interpolation, forward fill, and backward fill.
* Generates time-based features including hour, day of week, and an `is_weekend` indicator.

---

## Task 2: Model Training

This section covers training two deep learning models (LSTM and GRU) to predict traffic flow patterns using the preprocessed traffic data.

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
* Saves the best model based on validation loss to `saved/saved_lstm_model.keras`
* Evaluates performance on test data and generates prediction visualizations
* Results are saved to `results/test_result/` and `results/prediction/`

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
* Saves the best model based on validation loss to `saved/saved_gru_model.keras`
* Evaluates performance on test data and generates prediction visualizations
* Results are saved to `results/test_result/` and `results/prediction/`

### Model Architecture

Both models use a similar architecture:
* **Input:** Sequence of 96 time intervals (24 hours of 15-minute intervals)
* **Prediction:** Next 15-minute traffic flow value
* **Layers:** Two recurrent layers with dropout for regularization
* **Output:** Single value (predicted traffic volume)

### Model Outputs

After training, the following files are generated:
* `results/trained_models/gru_model.keras` - Trained GRU model
* `results/trained_models/lstm_model.keras` - Trained LSTM model
* `results/trained_models/gru_training_curve.png` - Model training graph of gru
* `results/trained_models/lstm_training_curve.png` - Model training graph of lstm