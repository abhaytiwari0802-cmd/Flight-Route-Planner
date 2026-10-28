"""Route calculation and network exploration endpoints."""
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, status

from ..models import RoutePlanRequest, RoutePlanResponse
from ..services.route_service import route_service
from ..services.data_service import data_service
from ..coordinates import get_airport_coordinates

router = APIRouter(prefix="/api", tags=["Planner & Network"])


@router.post("/plan", response_model=RoutePlanResponse)
def plan_route(payload: RoutePlanRequest):
    """Calculate shortest Dijkstra route and Yen alternative routes between airports."""
    response = route_service.plan_route(
        source=payload.source,
        destination=payload.destination,
        max_alternatives=payload.max_alternatives,
    )
    if not response.success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.message)
    return response


@router.get("/network")
def get_network_graph():
    """Retrieve full network topology (nodes with coordinates and edges) for map rendering."""
    airports = data_service.list_airports()
    routes = data_service.list_routes()

    nodes = [
        {
            "code": a["code"],
            "name": a["name"],
            "city": a["city"],
            "lat": a["lat"],
            "lon": a["lon"],
            "connections": a["routes_count"],
        }
        for a in airports
    ]

    edges = [
        {
            "source": r["source"],
            "destination": r["destination"],
            "distance_km": r["distance_km"],
            "travel_time_min": r["travel_time_min"],
            "source_coords": r["source_coords"],
            "destination_coords": r["destination_coords"],
        }
        for r in routes
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
    }
