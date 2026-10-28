"""Pydantic data models and API schemas."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class AirportBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=5, description="Airport IATA/ICAO code, e.g. JFK")
    name: str = Field(..., min_length=2, max_length=150, description="Full airport name")
    city: str = Field(..., min_length=2, max_length=100, description="City located in")

    @field_validator("code")
    @classmethod
    def format_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("name", "city")
    @classmethod
    def strip_text(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Field cannot be empty or whitespace.")
        return s


class AirportCreate(AirportBase):
    pass


class AirportUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    city: Optional[str] = Field(None, min_length=2, max_length=100)


class AirportResponse(AirportBase):
    lat: float
    lon: float
    routes_count: int = 0


class RouteBase(BaseModel):
    source: str = Field(..., min_length=2, max_length=5)
    destination: str = Field(..., min_length=2, max_length=5)
    distance_km: float = Field(..., gt=0, description="Distance in kilometers (must be positive)")
    travel_time_min: Optional[float] = Field(None, gt=0, description="Estimated flight duration in minutes")

    @field_validator("source", "destination")
    @classmethod
    def format_codes(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("destination")
    @classmethod
    def validate_different(cls, v: str, info) -> str:
        source = info.data.get("source")
        if source and v.strip().upper() == source.strip().upper():
            raise ValueError("Source and destination must be different.")
        return v.strip().upper()


class RouteCreate(RouteBase):
    pass


class RouteUpdate(BaseModel):
    distance_km: Optional[float] = Field(None, gt=0)
    travel_time_min: Optional[float] = Field(None, gt=0)


class RouteResponse(RouteBase):
    index: int
    source_city: str = ""
    destination_city: str = ""
    source_coords: List[float] = []
    destination_coords: List[float] = []


class RoutePlanRequest(BaseModel):
    source: str = Field(..., min_length=2, max_length=5)
    destination: str = Field(..., min_length=2, max_length=5)
    max_alternatives: int = Field(default=3, ge=1, le=5)

    @field_validator("source", "destination")
    @classmethod
    def format_codes(cls, v: str) -> str:
        return v.strip().upper()


class LegDetail(BaseModel):
    leg_number: int
    source: str
    destination: str
    source_city: str
    destination_city: str
    source_name: str
    destination_name: str
    distance_km: float
    travel_time_min: float
    formatted_duration: str
    start_coords: List[float]
    end_coords: List[float]
    arc_coordinates: List[List[float]]


class RouteOption(BaseModel):
    rank: int
    badge: str
    path: List[str]
    path_cities: List[str]
    total_distance_km: float
    total_travel_time_min: float
    formatted_duration: str
    layover_count: int
    layovers: List[str]
    is_direct: bool
    legs: List[LegDetail]
    full_arc_coordinates: List[List[float]]


class RoutePlanResponse(BaseModel):
    success: bool
    message: str
    source: str
    destination: str
    source_name: str
    destination_name: str
    best_route: Optional[RouteOption] = None
    alternative_routes: List[RouteOption] = []


class AnalyticsSummary(BaseModel):
    total_airports: int
    total_routes: int
    shortest_leg_km: float
    longest_leg_km: float
    average_leg_km: float
    average_duration_min: float
    network_density: float
    network_diameter: Optional[int] = None
    is_fully_connected: bool
    busiest_airports: List[Dict[str, Any]]
    distance_distribution: Dict[str, Any]
    scatter_data: List[Dict[str, Any]]
    longest_routes: List[Dict[str, Any]]
    shortest_routes: List[Dict[str, Any]]
