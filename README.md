# Traffic-based Route Guidance System (TBRGS) - GUI

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

