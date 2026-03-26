# Traffic-based Route Guidance System (TBRGS)

An interactive React GUI for visualizing SCATS intersections and displaying backend-generated route guidance based on ML traffic predictions.

## Overview

The GUI now uses the backend API directly for route guidance:
- `GET /api/graph` loads the SCATS nodes and edges shown on the map.
- `GET /api/routes` returns the top-k routes rendered in the cards, map, and segment breakdown panel.

Supported routing models in the UI:
- LightGBM
- GRU
- LSTM

## Tech Stack

- React
- TypeScript
- Vite
- Tailwind CSS
- Framer Motion
- React Leaflet

## Run Locally

1. Install frontend dependencies:
```bash
npm install
```

2. Install Python dependencies if needed:
```bash
pip install -r requirements.txt
```

3. Start the backend API in one terminal:
```bash
python -m backend.api_server
```

4. Start the frontend in another terminal:
```bash
npm run dev
```

5. Open the frontend URL shown by Vite, usually `http://localhost:5173`.

The frontend calls `http://127.0.0.1:8000` by default. You can override that with `VITE_API_BASE_URL`.

## Project Structure

- `backend/` - backend API, route engine, and model inference
- `backend/generated/` - generated SCATS graph JSON used by the API
- `src/pages/RouteGuidance.tsx` - page that fetches graph and route data
- `src/components/route-guidance/` - route controls, map, types, and details components

## Notes

- The route-guidance page no longer uses hard-coded mock routes.
- The page auto-loads graph data on open and fetches a default route once the graph is ready.
- Clicking `Find Routes` sends the current origin, destination, model, year, and top-k values to the backend.
