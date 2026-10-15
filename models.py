"""Domain models for airports and flight routes."""
import math
from typing import Optional


class Airport:
    """Represents an airport with a unique code."""
    def __init__(self, code: str, name: str, city: str):
        self.code = str(code).strip().upper()
        self.name = str(name).strip()
        self.city = str(city).strip()
        if not self.code or not self.name or not self.city:
            raise ValueError("Airport code, name, and city are required.")

    def __repr__(self):
        return f"Airport({self.code!r}, {self.name!r}, {self.city!r})"


class FlightRoute:
    """Represents a weighted connection between two airports."""
    def __init__(
        self, source: str, destination: str, distance_km: float,
        travel_time_min: Optional[float] = None
    ):
        self.source = str(source).strip().upper()
        self.destination = str(destination).strip().upper()
        try:
            self.distance_km = float(distance_km)
        except (TypeError, ValueError) as exc:
            raise ValueError("Distance must be a valid number.") from exc
        if not math.isfinite(self.distance_km) or self.distance_km <= 0:
            raise ValueError("Distance must be a finite positive number.")
        if not self.source or not self.destination:
            raise ValueError("Source and destination are required.")
        if self.source == self.destination:
            raise ValueError("Source and destination must be different.")
        if travel_time_min in (None, ""):
            self.travel_time_min = None
        else:
            try:
                self.travel_time_min = float(travel_time_min)
            except (TypeError, ValueError) as exc:
                raise ValueError("Travel time must be a valid number.") from exc
            if not math.isfinite(self.travel_time_min) or self.travel_time_min <= 0:
                raise ValueError("Travel time must be a finite positive number.")

    def __repr__(self):
        return (
            f"FlightRoute({self.source!r} - {self.destination!r}, "
            f"{self.distance_km} km, {self.travel_time_min} min)"
        )
