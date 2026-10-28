# ✈ Flight Route Planner — Modern Full-Stack Web Application

A full-stack, modern aviation web application and dashboard modernized from Tkinter/CustomTkinter into **FastAPI**, **Tailwind CSS**, **Leaflet.js**, and **Chart.js** with **pure CSV persistence** (`data/airports.csv`, `data/routes.csv`) — zero external databases.

---

## 🌟 Key Highlights

- **⚡ Backend**: High-performance **FastAPI** with automatic Swagger documentation at [`/docs`](http://127.0.0.1:8000/docs).
- **📂 Strict CSV Persistence**: Reads and writes directly to `data/airports.csv` and `data/routes.csv` via the existing validated `DataManager`.
- **🧭 Core Algorithms**:
  - **Dijkstra's Algorithm**: $O((V + E) \log V)$ shortest distance flight path discovery.
  - **Yen's $K$-Shortest Paths**: NetworkX candidate generation for multi-route comparison.
  - **Direct Flight vs Layover Analysis**: Automatic hop-by-hop flight leg breakdowns.
- **🗺 Interactive Leaflet.js Mapping**:
  - Dark Matter CartoDB tiles matching the cockpit dark theme.
  - Smooth **geodesic curved flight arcs** (quadratic Bezier curves).
  - **Animated airplane tracker** gliding continuously along the route.
  - Pulsating origin (cyan), destination (emerald), and layover (amber) airport markers.
- **📊 Analytics Studio (Chart.js)**:
  - Top 10 Busiest Airports by route degree.
  - Flight Distance Distribution Histogram.
  - Flight Distance vs Travel Time Scatter correlation.
  - Extremes: Top 5 Longest vs Top 5 Shortest connections.
  - Network density, graph diameter, and connectivity metrics.
- **🛠 Full CRUD Web Interfaces**:
  - Searchable and paginated directory for Airports and Routes.
  - Add, Edit, and Delete modals that immediately update the underlying CSV files.

---

## 📁 Suggested Project Folder Structure

```text
Flight-Route-Planner/
├── data/
│   ├── airports.csv              # CSV persistence: code, name, city
│   └── routes.csv                # CSV persistence: source, destination, distance_km, travel_time_min
├── web/
│   ├── __init__.py
│   ├── app.py                   # FastAPI initialization, CORS, routes & static mounting
│   ├── config.py                # Environment paths and server settings
│   ├── coordinates.py           # IATA airport coordinates resolver & curved arc calculations
│   ├── models.py                # Pydantic request & response schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── data_service.py      # DataManager wrapper strictly reading/writing CSVs
│   │   ├── route_service.py     # Dijkstra & Yen alternative path integration
│   │   └── analytics_service.py # Network KPIs & Chart.js data formatting
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── airports.py          # /api/airports (Listing, search autocomplete, CRUD)
│   │   ├── routes.py            # /api/routes (Route connections CRUD)
│   │   ├── planner.py           # /api/plan & /api/network
│   │   └── analytics.py         # /api/analytics
│   ├── static/
│   │   ├── css/
│   │   │   └── custom.css       # Cockpit dark theme, glassmorphism, radar pulse, animations
│   │   └── js/
│   │       ├── api.js           # Client API fetch wrapper
│   │       ├── map.js           # Leaflet.js map controller & geodesic arcs
│   │       ├── charts.js        # Chart.js visualizations
│   │       └── app.js           # Main dashboard controller & event handlers
│   └── templates/
│       └── index.html           # Tailwind CSS single-page cockpit dashboard
├── src/                         # Original core logic modules
│   ├── data_manager.py          # Core CSV persistence
│   ├── graph_manager.py         # NetworkX graph representation
│   ├── route_algorithms.py      # Dijkstra and Yen pathfinding algorithms
│   ├── analytics.py             # Route statistics
│   ├── models.py                # Domain classes (Airport, FlightRoute)
│   └── customtkinter_gui.py     # Original desktop GUI
├── tests/
│   ├── test_data_manager.py     # CSV tests
│   ├── test_route_algorithms.py # Pathfinding algorithm tests
│   └── test_web_api.py          # FastAPI web endpoint tests
├── run_web.py                   # Single-command runner for the web application
├── main.py                      # Original desktop app runner
└── requirements.txt             # Project dependencies
```

---

## 🚀 Quickstart Guide

### 1. Install Dependencies

Ensure Python 3.10+ is installed, then install the required packages:

```bash
pip install -r requirements.txt
```

*(Requirements include `fastapi`, `uvicorn`, `pandas`, `networkx`, `numpy`)*

### 2. Run the Modern Web Application

Run the server with auto-reload:

```bash
python run_web.py
```

Or run via Uvicorn directly:

```bash
uvicorn web.app:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser and navigate to:
- **Web Dashboard**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Run the Desktop App (Optional)

The desktop application remains intact:

```bash
python main.py
```

### 4. Run the Test Suite

```bash
pytest tests
```
*(All 21 unit & integration tests validate data persistence, algorithms, and web endpoints)*
