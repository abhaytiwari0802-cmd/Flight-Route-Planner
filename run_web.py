"""Launcher for Flight Route Planner Web Application.

Run this file directly in PyCharm (Right-Click -> Run 'run_web')
or from terminal: python run_web.py
"""
import sys
import os
import argparse
from pathlib import Path

# Set root directory to sys.path and environment PYTHONPATH for reload subprocesses
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure PYTHONPATH environment variable includes ROOT_DIR for uvicorn reloader child processes
existing_pythonpath = os.environ.get("PYTHONPATH", "")
if str(ROOT_DIR) not in existing_pythonpath.split(os.pathsep):
    os.environ["PYTHONPATH"] = (
        f"{str(ROOT_DIR)}{os.pathsep}{existing_pythonpath}"
        if existing_pythonpath
        else str(ROOT_DIR)
    )

import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Run Flight Route Planner Web App")
    parser.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    args = parser.parse_args()

    reload_flag = not args.no_reload

    print("\n" + "=" * 65)
    print(" ✈  FLIGHT ROUTE PLANNER — MODERN WEB APPLICATION")
    print("=" * 65)
    print(f" • Local Web Dashboard:   http://{args.host}:{args.port}")
    print(f" • Interactive API Docs:  http://{args.host}:{args.port}/docs")
    print(" • Data Persistence:      Direct CSV read/write (data/airports.csv, data/routes.csv)")
    print(" • Algorithms:            Dijkstra Shortest Paths & Yen Alternative Routes")
    print(" • Mapping:               Leaflet.js Geodesic Arcs & CartoDB Dark")
    print("=" * 65 + "\n")

    uvicorn.run(
        "web.app:app",
        host=args.host,
        port=args.port,
        reload=reload_flag,
        app_dir=str(ROOT_DIR),
    )


if __name__ == "__main__":
    main()
