"""Flight routes and network connection endpoints (CRUD)."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status

from ..models import RouteResponse, RouteCreate, RouteUpdate
from ..services.data_service import data_service

router = APIRouter(prefix="/api/routes", tags=["Routes"])


@router.get("", response_model=List[RouteResponse])
def get_all_routes():
    """Retrieve all flight routes directly from routes.csv."""
    return data_service.list_routes()


@router.post("", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
def create_route(payload: RouteCreate):
    """Add a new flight route connection directly to routes.csv."""
    try:
        new_route = data_service.add_route(
            source=payload.source,
            destination=payload.destination,
            distance_km=payload.distance_km,
            travel_time_min=payload.travel_time_min,
        )
        return new_route
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.put("/{index}", response_model=RouteResponse)
def update_route(index: int, payload: RouteUpdate):
    """Update route distance or travel time in routes.csv."""
    try:
        updated = data_service.update_route(
            index=index,
            distance_km=payload.distance_km,
            travel_time_min=payload.travel_time_min,
        )
        return updated
    except IndexError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/{index}", status_code=status.HTTP_200_OK)
def delete_route(index: int):
    """Delete route connection by index from routes.csv."""
    try:
        data_service.delete_route(index=index)
        return {"success": True, "message": f"Route index {index} successfully deleted."}
    except IndexError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
