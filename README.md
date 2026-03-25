# Traffic-based Route Guidance System (TBRGS)

An advanced, interactive web-based graphical user interface for visualizing and calculating optimal travel routes using machine learning-predicted traffic data.

## 🌟 Overview

The **TBRGS GUI** provides a comprehensive routing interface to explore the Swinburne Introduction to AI Assignment 2B project. It allows users to:
* Select different Machine Learning models (XGBoost, GRU, LSTM, Random Forest) for route evaluation.
* Interactively select origins and destinations on a mapped city grid using SCATS IDs.
* Visualize the optimal route as well as Alternative Top-K Routes with smooth animations.
* View detailed statistics including estimated time, distance, and traffic congestion levels.

## 🚀 Features

* **Interactive City Map**: View nodes, edges, and real-time route rendering.
* **Algorithm Selection**: Compare how different ML models affect the routed path.
* **Top-K Routing**: Select the number of alternative routes to generate and visualize.
* **Modern UI**: Clean and responsive design using Tailwind CSS and Framer Motion for a premium feel.

## 🛠️ Technology Stack

* **Framework**: [React](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
* **Build Tool**: [Vite](https://vitejs.dev/)
* **Styling**: [Tailwind CSS](https://tailwindcss.com/)
* **Animations**: [Framer Motion](https://www.framer.com/motion/)
* **Icons**: [Lucide React](https://lucide.dev/)

## 📦 Installation

Ensure you have [Node.js](https://nodejs.org/) installed on your machine.

**1. Navigate to the GUI folder (if you aren't already there):**
```bash
cd tbrgs-gui
```

**2. Install all necessary dependencies:**
```bash
npm install
```

## 🚦 How to Run the Application

**1. Start the development server:**
```bash
npm run dev
```

**2. Open your browser:**
Once the server starts, it will provide a local URL (usually `http://localhost:5173`). Click or copy this link into your web browser to interact with the GUI.

## 🏗️ Project Structure
* `src/components/route-guidance/` - Contains the core map, controls, and route detail viewing components.
* `src/pages/` - Main page views (Dashboard, Data Processing, Route Guidance).
* `src/App.tsx` - Root application routing.

---

## Team Members

| Name                  | Student ID | Task & Responsibility                                                                          |
| :-------------------- | :--------- | :--------------------------------------------------------------------------------------------- |
| Bui Quang Doan        | 104993227  | Data Processing & Dataset Preparation for 2006                                                 |
| Do Gia Huy (Leader)   | 104988294  | ML Implementation (LSTM/GRU), Model Evaluation, Data Processing & Dataset Preparation for 2014 |
| Huynh Doan Hoang Minh | 104777308  | ML Implementation (LightGBM), Model Evaluation, Backend, Frontend Supporter                    |
| Le Thanh Nam          | 104999380  | System Integration, Travel Time Estimation & GUI                                               |

## Project Overview

- Goal: Build a traffic-based route guidance system for the City of Boroondara.
- Data: Historical SCATS traffic flow data from October 2006 (training) plus October 2014 (held-out temporal test).
- Models: LSTM, GRU, and LightGBM models to forecast 15-minute traffic volume.
- Routing: Forecasts will later be converted to travel times for A\* routing (not covered here).

---

## Prerequisites

- Python 3.12 or later
- Install dependencies: `pip install -r requirements.txt`

---

## Datasets & Split Strategy

- 2006 dataset is split **70/10/20** into train/validation/test using sliding 96-step windows per site.
- Early stopping and learning-rate scheduling monitor the **2006 validation** split only.
- The **2014 dataset is never used for training**. It is a temporal generalisation check over an 8-year gap.
- Feature scaling: `MinMaxScaler` is **fit on 2006 training only** and reused everywhere.
- Road name encoding: `LabelEncoder` is fit on 2006; unseen 2014 road names map to **-1** to avoid leakage.

---

## Data Preparation

- 2006 processing  
  `python -m src.process_2006`  
  Output: `data/processed/2006_processed.csv`

- 2014 processing (uses detector-direction lookup and 2006 metadata)  
  `python -m src.process_2014`  
  Output: `data/processed/2014_processed.csv`

---

## Model Training (2006 only)

The sequence models train on `data/processed/2006_processed.csv` with 96-step input sequences and 1-step (15-minute) forecasts. LightGBM uses the same dataset but converts each movement history into lag-based tabular rows.

- LSTM: `python -m models.lstm_model`
- GRU : `python -m models.gru_model`
- LightGBM: `python -m models.lightgbm_model`

Artifacts: saved models and training curves in `results/trained_models/`.

---

## Prediction Pipeline

Predictions are generated on **full continuous datasets** to preserve 96-step sequence integrity before any filtering.

- Run on 2014 (temporal generalisation):  
  `python -m src.predict --data 2014`

- Run on 2006 (in-domain check):  
  `python -m src.predict --data 2006`

Outputs: `results/predictions/{year}_predictions.csv` with columns  
`datetime, scats_number, location, hour, day_of_week, is_weekend, actual, predicted_lstm, predicted_gru, predicted_lightgbm`.

---

## Scenario Tests (post-prediction)

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

Example commands:

- Default (2014 data, all models):  
  `python -m src.test_runner --test T01-morning_peak_hour`
- Specify model:  
  `python -m src.test_runner --test T06-high_vol_intersection --model lstm`
- Use 2006 predictions:  
  `python -m src.test_runner --test T01-morning_peak_hour --data 2006`

Metrics (MAE, RMSE, MAPE) are written to `results/test_result/{test}_metrics.json`; plots go to `results/test_graphs/`.
