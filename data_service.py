"""Data service interacting strictly with CSV files through DataManager."""
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import networkx as nx

from ..config import AIRPORTS_CSV, ROUTES_CSV, PROJECT_DIR

# Ensure src is in python path
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src.models import Airport, FlightRoute
from src.data_manager import DataManager
from src.graph_manager import GraphManager
from ..coordinates import get_airport_coordinates


class DataService:
    def __init__(self, airports_csv: Path = AIRPORTS_CSV, routes_csv: Path = ROUTES_CSV):
        self.dm = DataManager(airports_csv=airports_csv, routes_csv=routes_csv)

    def get_airports_df(self) -> pd.DataFrame:
        """Load fresh airports DataFrame from airports.csv."""
        return self.dm.load_airports()

    def get_routes_df(self) -> pd.DataFrame:
        """Load fresh routes DataFrame from routes.csv."""
        return self.dm.load_routes()

    def get_graph(self) -> nx.Graph:
        """Build and return updated NetworkX graph from current CSVs."""
        gm = GraphManager(self.get_airports_df(), self.get_routes_df())
        return gm.to_networkx()

    def list_airports(self) -> List[Dict[str, Any]]:
        """List all airports enriched with coordinates and route connections."""
        airports_df = self.get_airports_df()
        routes_df = self.get_routes_df()
        
        # Calculate route degree counts
        route_counts: Dict[str, int] = {}
        for _, row in routes_df.iterrows():
            src = str(row["source"]).strip().upper()
            dst = str(row["destination"]).strip().upper()
            route_counts[src] = route_counts.get(src, 0) + 1
            route_counts[dst] = route_counts.get(dst, 0) + 1

        result = []
        for _, row in airports_df.iterrows():
            code = str(row["code"]).strip().upper()
            name = str(row["name"]).strip()
            city = str(row["city"]).strip()
            lat, lon = get_airport_coordinates(code)
            result.append({
                "code": code,
                "name": name,
                "city": city,
                "lat": lat,
                "lon": lon,
                "routes_count": route_counts.get(code, 0),
            })
        return sorted(result, key=lambda x: x["code"])

    def search_airports(self, query: str) -> List[Dict[str, Any]]:
        """Filter airports matching query against code, name, or city."""
        q = query.strip().upper()
        all_airports = self.list_airports()
        if not q:
            return all_airports[:10]

        matches = []
        for a in all_airports:
            if (
                q in a["code"]
                or q in a["name"].upper()
                or q in a["city"].upper()
            ):
                matches.append(a)
        return matches

    def get_airport(self, code: str) -> Optional[Dict[str, Any]]:
        code_upper = str(code).strip().upper()
        for a in self.list_airports():
            if a["code"] == code_upper:
                return a
        return None

    def add_airport(self, code: str, name: str, city: str) -> Dict[str, Any]:
        airport = Airport(code=code, name=name, city=city)
        self.dm.add_airport(airport)
        lat, lon = get_airport_coordinates(airport.code)
        return {
            "code": airport.code,
            "name": airport.name,
            "city": airport.city,
            "lat": lat,
            "lon": lon,
            "routes_count": 0,
        }

    def update_airport(self, code: str, name: Optional[str] = None, city: Optional[str] = None) -> Dict[str, Any]:
        self.dm.update_airport(code=code, name=name, city=city)
        return self.get_airport(code) or {}

    def delete_airport(self, code: str) -> bool:
        self.dm.delete_airport(code=code)
        return True

    def list_routes(self) -> List[Dict[str, Any]]:
        """List all routes with index, airport details, and endpoints coordinates."""
        routes_df = self.get_routes_df()
        airports_df = self.get_airports_df()
        
        city_map = dict(zip(airports_df["code"].str.upper(), airports_df["city"]))
        name_map = dict(zip(airports_df["code"].str.upper(), airports_df["name"]))

        result = []
        for idx, row in routes_df.iterrows():
            src = str(row["source"]).strip().upper()
            dst = str(row["destination"]).strip().upper()
            dist = float(row["distance_km"]) if pd.notna(row["distance_km"]) else 0.0
            time = float(row["travel_time_min"]) if pd.notna(row["travel_time_min"]) and row["travel_time_min"] != "" else None
            
            src_lat, src_lon = get_airport_coordinates(src)
            dst_lat, dst_lon = get_airport_coordinates(dst)

            result.append({
                "index": int(idx),
                "source": src,
                "destination": dst,
                "source_city": city_map.get(src, src),
                "destination_city": city_map.get(dst, dst),
                "source_name": name_map.get(src, ""),
                "destination_name": name_map.get(dst, ""),
                "distance_km": dist,
                "travel_time_min": time,
                "source_coords": [src_lat, src_lon],
                "destination_coords": [dst_lat, dst_lon],
            })
        return result

    def add_route(self, source: str, destination: str, distance_km: float, travel_time_min: Optional[float] = None) -> Dict[str, Any]:
        route = FlightRoute(source=source, destination=destination, distance_km=distance_km, travel_time_min=travel_time_min)
        self.dm.add_route(route)
        routes = self.list_routes()
        return routes[-1] if routes else {}

    def update_route(self, index: int, distance_km: Optional[float] = None, travel_time_min: Optional[float] = None) -> Dict[str, Any]:
        self.dm.update_route(index=index, distance_km=distance_km, travel_time_min=travel_time_min)
        routes = self.list_routes()
        if 0 <= index < len(routes):
            return routes[index]
        return {}

    def delete_route(self, index: int) -> bool:
        self.dm.delete_route(index=index)
        return True


# Singleton instance
data_service = DataService()
