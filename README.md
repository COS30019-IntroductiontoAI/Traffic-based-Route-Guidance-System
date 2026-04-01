# Traffic-Based Route Guidance System (TBRGS)

## Team Members

| Name                  | Student ID | Task & Responsibility                                                                          |
| :-------------------- | :--------- | :--------------------------------------------------------------------------------------------- |
| Bui Quang Doan        | 104993227  | Data Processing & Dataset Preparation for 2006, Frontend Support                               |
| Do Gia Huy (Leader)   | 104988294  | ML Implementation (LSTM/GRU), Model Evaluation, Data Processing & Dataset Preparation for 2014 |
| Huynh Doan Hoang Minh | 104777308  | ML Implementation (LightGBM), Model Evaluation, Backend, Frontend Supporter                    |
| Le Thanh Nam          | 104999380  | System Integration, Travel Time Estimation & GUI                                               |

## Project Overview

- Goal: Build a traffic-based route guidance system for the City of Boroondara.
- Data: Historical SCATS traffic flow data from October 2006 (training) plus October 2014 (held-out temporal test).
- Models: LSTM, GRU, and LightGBM models to forecast 15-minute traffic volume.
- Routing: Forecasts are converted to travel times for A* routing.

## Prerequisites

- Python 3.12 or later
- Node.js 18 or later

## Run the GUI application locally

1. Install dependencies (from project root):

   ```bash
   pip install -r requirements.txt
   pip install -r backend/requirements.txt
   npm install
   ```

2. Ensure prediction CSVs exist for the backend:
   - Copy prepared files to `results/predictions/2006_predictions.csv` and `results/predictions/2014_predictions.csv`, **or** generate them via the steps in [Test the model locally (src)](#test-the-model-locally-src).

3. (Optional) Smoke test the backend engine:

   ```bash
   python -m backend.main
   ```

   Runs a quick route query (node 970 → 4043) and prints JSON.

4. Start the backend API server (keep it running):

   ```bash
   python -m backend.api_server
   ```

   API base: http://127.0.0.1:8000

5. Start the frontend dev server (new terminal):

   ```bash
   npm run dev
   ```

   App: http://localhost:5173 (or next free port)

> Both backend and frontend must stay running for the full GUI experience.

## Test the model locally (src)

Use the `src` pipelines to process data, train models, generate predictions, and run evaluation suites. If you already installed Python dependencies in the GUI section, reuse that environment.

### Datasets & split strategy

- 2006 dataset is split **70/10/20** into train/validation/test using sliding 96-step windows per site.
- Early stopping and learning-rate scheduling monitor the **2006 validation** split only.
- The **2014 dataset is never used for training**. It is a temporal generalisation check over an 8-year gap.
- Feature scaling: `MinMaxScaler` is **fit on 2006 training only** and reused everywhere.
- Road name encoding: `LabelEncoder` is fit on 2006; unseen 2014 road names map to **-1** to avoid leakage.

### Data preparation

- 2006 processing:

   ```bash
   python -m src.process_2006
   ```

   Output: `data/processed/2006_processed.csv`

- 2014 processing (uses detector-direction lookup and 2006 metadata):

   ```bash
   python -m src.process_2014
   ```

   Output: `data/processed/2014_processed.csv`

### Model training (2006 only)

The sequence models train on `data/processed/2006_processed.csv` with 96-step input sequences and 1-step (15-minute) forecasts. LightGBM converts each movement history into lag-based tabular rows.

- LSTM:

   ```bash
   python -m src.models.lstm_model
   ```

- GRU:

   ```bash
   python -m src.models.gru_model
   ```

- LightGBM:

   ```bash
   python -m src.models.lightgbm_model
   ```

Artifacts: saved models and training curves in `results/trained_models/`.

### Prediction pipeline

Predictions are generated on **full continuous datasets** to preserve 96-step sequence integrity before any filtering.

- Run on 2014 (temporal generalisation):

   ```bash
   python -m src.predict --data 2014
   ```

- Run on 2006 (in-domain check):

   ```bash
   python -m src.predict --data 2006
   ```

Outputs: `results/predictions/{year}_predictions.csv` with columns `datetime, scats_number, location, hour, day_of_week, is_weekend, actual, predicted_lstm, predicted_gru, predicted_lightgbm`.

### Scenario tests (post-prediction)

`src/test_runner.py` filters the **precomputed predictions CSVs** (no model re-run) so every evaluated point comes from a valid 96-step window.

Test Case Descriptions:

| ID  | Name                         | Scenario                       |
| :-: | :--------------------------- | :----------------------------- |
| T01 | Morning Peak Hour            | Weekday 7:00-9:45 AM           |
| T02 | Evening Peak Hour            | Weekday 4:00-6:45 PM           |
| T03 | Late Night Low Volume        | 11:00 PM-2:45 AM               |
| T04 | Weekday vs Weekend           | All weekend intervals          |
| T05 | Mon Morning vs Fri Afternoon | Start vs end of week           |
| T06 | High Volume Intersection     | Busiest SCATS site             |
| T07 | Low Volume Intersection      | Quietest SCATS site            |
| T08 | Full Monday                  | All 96 intervals on Mondays    |
| T09 | Full Week                    | All intervals for busiest site |
| T10 | Transition Period            | 6:00-8:45 AM ramp-up           |

Usage:

```bash
# Run all tests and aggregate to CSV (2014 data)
python -m src.test_runner --data 2014

# Run single test
python -m src.test_runner --test T01 --data 2014

# Run specific model
python -m src.test_runner --test T06 --model lstm --data 2014
```

Outputs:
- Aggregated metrics: `results/test_results/test_metrics_full.csv`
- Individual plots: `results/test_graphs/T01/lstm_predictions.png`, etc.

### Stratified dataset test runner (20% test split only)

`src/test_stratified.py` runs the same 10 test cases but **only on the 20% test split** of the 2006 dataset (the portion held out during model training/validation).

Usage:

```bash
python -m src.test_stratified
```

This will:
1. Extract the 20% test split from 2006 dataset using time-based boundaries
2. Load full 2006 predictions and filter to test split
3. Run all 10 test cases on the test split
4. Compute metrics for LSTM, GRU, and LightGBM

Outputs:
- Aggregated metrics: `results/test_results/test_split_metrics.csv`
- Individual plots: `results/test_graphs/T01/lstm_predictions.png`, etc. (split versions)
