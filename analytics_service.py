"""Analytics service generating network KPIs and Chart.js datasets."""
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import networkx as nx

from .data_service import data_service
from ..models import AnalyticsSummary


class AnalyticsService:
    def __init__(self, data_svc=data_service):
        self.data_service = data_svc

    def get_summary(self) -> AnalyticsSummary:
        """Calculate complete network statistics and Chart.js visualization data."""
        airports_df = self.data_service.get_airports_df()
        routes_df = self.data_service.get_routes_df()
        G = self.data_service.get_graph()

        total_airports = len(airports_df)
        total_routes = len(routes_df)

        distances = pd.to_numeric(routes_df["distance_km"], errors="coerce").dropna().values
        times = pd.to_numeric(routes_df["travel_time_min"], errors="coerce").dropna().values

        shortest_leg = float(np.min(distances)) if len(distances) > 0 else 0.0
        longest_leg = float(np.max(distances)) if len(distances) > 0 else 0.0
        avg_leg = float(np.mean(distances)) if len(distances) > 0 else 0.0
        avg_time = float(np.mean(times)) if len(times) > 0 else 0.0

        # Network Graph Theory Metrics
        num_nodes = G.number_of_nodes()
        density = nx.density(G) if num_nodes > 1 else 0.0
        is_connected = nx.is_connected(G) if num_nodes > 1 else False
        diameter = nx.diameter(G) if is_connected and num_nodes > 1 else None

        # 1. Busiest Airports (by degree)
        airport_names = dict(zip(airports_df["code"].str.upper(), airports_df["name"]))
        airport_cities = dict(zip(airports_df["code"].str.upper(), airports_df["city"]))
        
        degrees = sorted(G.degree(), key=lambda x: x[1], reverse=True)[:10]
        busiest_airports = [
            {
                "code": code,
                "name": airport_names.get(code, code),
                "city": airport_cities.get(code, code),
                "connections": degree,
            }
            for code, degree in degrees
        ]

        # 2. Distance Distribution Histogram
        bin_specs = [
            ("0–500 km", 0, 500),
            ("501–1,000 km", 500, 1000),
            ("1,001–1,500 km", 1000, 1500),
            ("1,501–2,000 km", 1500, 2000),
            ("2,001–3,000 km", 2000, 3000),
            ("3,000+ km", 3000, float("inf")),
        ]
        
        labels = [b[0] for b in bin_specs]
        counts = [0] * len(bin_specs)

        for d in distances:
            for idx, (_, low, high) in enumerate(bin_specs):
                if low <= d < high:
                    counts[idx] += 1
                    break

        distance_distribution = {
            "labels": labels,
            "counts": counts,
        }

        # 3. Distance vs Travel Time Scatter Points
        scatter_data: List[Dict[str, Any]] = []
        for _, row in routes_df.iterrows():
            try:
                dist = float(row["distance_km"])
                time = float(row["travel_time_min"])
                if dist > 0 and time > 0:
                    scatter_data.append({
                        "x": dist,
                        "y": time,
                        "label": f"{row['source']} → {row['destination']}",
                    })
            except (ValueError, TypeError, KeyError):
                continue

        # 4. Longest & Shortest Routes
        valid_routes = routes_df.dropna(subset=["distance_km"]).copy()
        valid_routes["distance_km"] = pd.to_numeric(valid_routes["distance_km"])

        sorted_longest = valid_routes.sort_values(by="distance_km", ascending=False).head(5)
        longest_routes = [
            {
                "route": f"{r['source']} ➔ {r['destination']}",
                "distance_km": float(r["distance_km"]),
                "travel_time_min": float(r["travel_time_min"]) if pd.notna(r["travel_time_min"]) else None,
            }
            for _, r in sorted_longest.iterrows()
        ]

        sorted_shortest = valid_routes.sort_values(by="distance_km", ascending=True).head(5)
        shortest_routes = [
            {
                "route": f"{r['source']} ➔ {r['destination']}",
                "distance_km": float(r["distance_km"]),
                "travel_time_min": float(r["travel_time_min"]) if pd.notna(r["travel_time_min"]) else None,
            }
            for _, r in sorted_shortest.iterrows()
        ]

        return AnalyticsSummary(
            total_airports=total_airports,
            total_routes=total_routes,
            shortest_leg_km=shortest_leg,
            longest_leg_km=longest_leg,
            average_leg_km=round(avg_leg, 1),
            average_duration_min=round(avg_time, 1),
            network_density=round(density, 4),
            network_diameter=diameter,
            is_fully_connected=is_connected,
            busiest_airports=busiest_airports,
            distance_distribution=distance_distribution,
            scatter_data=scatter_data,
            longest_routes=longest_routes,
            shortest_routes=shortest_routes,
        )


analytics_service = AnalyticsService()
