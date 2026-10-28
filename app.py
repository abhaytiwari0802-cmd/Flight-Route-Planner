"""Main FastAPI application for Flight Route Planner."""
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .config import STATIC_DIR, TEMPLATES_DIR
from .routers import airports_router, routes_router, planner_router, analytics_router

app = FastAPI(
    title="Flight Route Planner API",
    description="Full-stack Flight Route Planner powered by FastAPI, Dijkstra shortest paths, Leaflet.js, and Chart.js with pure CSV persistence.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include Routers
app.include_router(airports_router)
app.include_router(routes_router)
app.include_router(planner_router)
app.include_router(analytics_router)


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """Serve the single-page dashboard application."""
    index_path = TEMPLATES_DIR / "index.html"
    return FileResponse(index_path)


@app.get("/health")
def healthcheck():
    """Health check endpoint."""
    return {"status": "ok", "app": "Flight Route Planner"}
