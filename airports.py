"""Airport API endpoints for listing, auto-suggestions, and CRUD."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from ..models import AirportResponse, AirportCreate, AirportUpdate
from ..services.data_service import data_service

router = APIRouter(prefix="/api/airports", tags=["Airports"])


@router.get("", response_model=List[AirportResponse])
def get_all_airports():
    """Retrieve all airports loaded directly from airports.csv."""
    return data_service.list_airports()


@router.get("/search", response_model=List[AirportResponse])
def search_airports(q: str = Query("", description="Search query by code, name, or city")):
    """Auto-suggestion endpoint matching airport code, name, or city."""
    return data_service.search_airports(q)


@router.get("/{code}", response_model=AirportResponse)
def get_airport(code: str):
    """Retrieve details for a single airport."""
    airport = data_service.get_airport(code)
    if not airport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Airport '{code.upper()}' not found in airports.csv."
        )
    return airport


@router.post("", response_model=AirportResponse, status_code=status.HTTP_201_CREATED)
def create_airport(payload: AirportCreate):
    """Add a new airport directly to airports.csv."""
    try:
        new_airport = data_service.add_airport(
            code=payload.code,
            name=payload.name,
            city=payload.city
        )
        return new_airport
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.put("/{code}", response_model=AirportResponse)
def update_airport(code: str, payload: AirportUpdate):
    """Update airport name and city in airports.csv."""
    try:
        updated = data_service.update_airport(
            code=code,
            name=payload.name,
            city=payload.city
        )
        return updated
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/{code}", status_code=status.HTTP_200_OK)
def delete_airport(code: str):
    """Delete airport from airports.csv and remove any connected routes in routes.csv."""
    try:
        data_service.delete_airport(code)
        return {"success": True, "message": f"Airport '{code.upper()}' and its routes successfully deleted."}
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
