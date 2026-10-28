"""Validated CSV persistence for airport and route records."""
from pathlib import Path
import math
import pandas as pd
from .models import Airport, FlightRoute

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
AIRPORTS_CSV = DATA_DIR / "airports.csv"
ROUTES_CSV = DATA_DIR / "routes.csv"

AIRPORT_COLUMNS = ["code", "name", "city"]
ROUTE_COLUMNS = ["source", "destination", "distance_km", "travel_time_min"]


class DataManager:
    """Load, validate, modify, and persist airport and route CSV files."""
    def __init__(self, airports_csv: Path = AIRPORTS_CSV, routes_csv: Path = ROUTES_CSV):
        self.airports_csv = Path(airports_csv)
        self.routes_csv = Path(routes_csv)
        self._ensure_data_files()

    def _ensure_data_files(self):
        self.airports_csv.parent.mkdir(parents=True, exist_ok=True)
        self.routes_csv.parent.mkdir(parents=True, exist_ok=True)
        if not self.airports_csv.exists():
            pd.DataFrame(columns=AIRPORT_COLUMNS).to_csv(self.airports_csv, index=False)
        if not self.routes_csv.exists():
            pd.DataFrame(columns=ROUTE_COLUMNS).to_csv(self.routes_csv, index=False)

    def load_airports(self) -> pd.DataFrame:
        df = pd.read_csv(self.airports_csv, dtype=str).fillna("")
        for column in AIRPORT_COLUMNS:
            if column not in df.columns:
                df[column] = ""
        df = df[AIRPORT_COLUMNS]
        df["code"] = df["code"].str.strip().str.upper()
        df["name"] = df["name"].str.strip()
        df["city"] = df["city"].str.strip()
        return df

    def load_routes(self) -> pd.DataFrame:
        df = pd.read_csv(self.routes_csv).fillna("")
        for column in ROUTE_COLUMNS:
            if column not in df.columns:
                df[column] = ""
        df = df[ROUTE_COLUMNS]
        df["source"] = df["source"].astype(str).str.strip().str.upper()
        df["destination"] = df["destination"].astype(str).str.strip().str.upper()
        df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce")
        df["travel_time_min"] = pd.to_numeric(df["travel_time_min"], errors="coerce")
        return df

    def save_airports(self, df: pd.DataFrame):
        df[AIRPORT_COLUMNS].to_csv(self.airports_csv, index=False)

    def save_routes(self, df: pd.DataFrame):
        df[ROUTE_COLUMNS].to_csv(self.routes_csv, index=False)

    def add_airport(self, airport: Airport):
        df = self.load_airports()
        if airport.code in df["code"].values:
            raise ValueError(f"Airport code {airport.code} already exists.")
        new_row = pd.DataFrame([{
            "code": airport.code, "name": airport.name, "city": airport.city
        }], columns=AIRPORT_COLUMNS)
        df = pd.concat([df, new_row], ignore_index=True)
        self.save_airports(df)
        return df

    def update_airport(self, code: str, name=None, city=None):
        code = str(code).strip().upper()
        df = self.load_airports()
        if code not in df["code"].values:
            raise KeyError(f"Airport {code} not found.")
        if name is not None:
            name = str(name).strip()
            if not name:
                raise ValueError("Airport name cannot be empty.")
            df.loc[df["code"] == code, "name"] = name
        if city is not None:
            city = str(city).strip()
            if not city:
                raise ValueError("Airport city cannot be empty.")
            df.loc[df["code"] == code, "city"] = city
        self.save_airports(df)
        return df

    def delete_airport(self, code: str):
        code = str(code).strip().upper()
        airports = self.load_airports()
        if code not in airports["code"].values:
            raise KeyError(f"Airport {code} not found.")
        airports = airports[airports["code"] != code].reset_index(drop=True)
        routes = self.load_routes()
        routes = routes[
            (routes["source"] != code) & (routes["destination"] != code)
        ].reset_index(drop=True)
        self.save_airports(airports)
        self.save_routes(routes)
        return airports, routes

    def add_route(self, route: FlightRoute):
        airports = self.load_airports()
        codes = set(airports["code"].values)
        if route.source not in codes or route.destination not in codes:
            raise KeyError("Source or destination airport code not found.")
        df = self.load_routes()
        same_pair = (
            ((df["source"] == route.source) & (df["destination"] == route.destination)) |
            ((df["source"] == route.destination) & (df["destination"] == route.source))
        )
        if same_pair.any():
            raise ValueError("A route already exists between these airports.")
        row = pd.DataFrame([{
            "source": route.source,
            "destination": route.destination,
            "distance_km": route.distance_km,
            "travel_time_min": route.travel_time_min,
        }], columns=ROUTE_COLUMNS)
        df = pd.concat([df, row], ignore_index=True)
        self.save_routes(df)
        return df

    def update_route(self, index: int, distance_km=None, travel_time_min=None):
        df = self.load_routes()
        if not isinstance(index, int) or index < 0 or index >= len(df):
            raise IndexError("Route index out of range.")
        if distance_km is not None:
            distance = float(distance_km)
            if not math.isfinite(distance) or distance <= 0:
                raise ValueError("Distance must be a finite positive number.")
            df.at[index, "distance_km"] = distance
        if travel_time_min is not None:
            if travel_time_min == "":
                df.at[index, "travel_time_min"] = float("nan")
            else:
                travel_time = float(travel_time_min)
                if not math.isfinite(travel_time) or travel_time <= 0:
                    raise ValueError("Travel time must be a finite positive number.")
                df.at[index, "travel_time_min"] = travel_time
        self.save_routes(df)
        return df

    def delete_route(self, index: int):
        df = self.load_routes()
        if not isinstance(index, int) or index < 0 or index >= len(df):
            raise IndexError("Route index out of range.")
        df = df.drop(df.index[index]).reset_index(drop=True)
        self.save_routes(df)
        return df
