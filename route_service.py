"""Route calculation service integrating Dijkstra and alternative paths algorithms."""
from typing import List, Dict, Any, Optional
import networkx as nx

from src.route_algorithms import dijkstra, build_adj_from_nx, find_alternative_paths
from .data_service import data_service
from ..coordinates import get_airport_coordinates, calculate_flight_arc
from ..models import RoutePlanResponse, RouteOption, LegDetail


def format_duration(minutes: Optional[float]) -> str:
    """Format minutes into human-readable hours and minutes."""
    if not minutes or minutes <= 0:
        return "—"
    hours, mins = divmod(int(round(minutes)), 60)
    if hours > 0 and mins > 0:
        return f"{hours}h {mins}m"
    elif hours > 0:
        return f"{hours}h"
    return f"{mins} min"


class RouteService:
    def __init__(self, data_svc=data_service):
        self.data_service = data_svc

    def plan_route(self, source: str, destination: str, max_alternatives: int = 3) -> RoutePlanResponse:
        """Calculate optimal and alternative flight routes between two airports."""
        src = source.strip().upper()
        dst = destination.strip().upper()

        if src == dst:
            return RoutePlanResponse(
                success=False,
                message="Origin and destination must be different airports.",
                source=src,
                destination=dst,
                source_name="",
                destination_name="",
            )

        airports_df = self.data_service.get_airports_df()
        airport_names = dict(zip(airports_df["code"].str.upper(), airports_df["name"]))
        airport_cities = dict(zip(airports_df["code"].str.upper(), airports_df["city"]))

        src_name = airport_names.get(src, src)
        dst_name = airport_names.get(dst, dst)

        G = self.data_service.get_graph()

        if src not in G or dst not in G:
            missing = []
            if src not in G: missing.append(src)
            if dst not in G: missing.append(dst)
            return RoutePlanResponse(
                success=False,
                message=f"Airport code(s) not found in network: {', '.join(missing)}",
                source=src,
                destination=dst,
                source_name=src_name,
                destination_name=dst_name,
            )

        if not nx.has_path(G, src, dst):
            return RoutePlanResponse(
                success=False,
                message=f"No flight connection route available between {src} and {dst}.",
                source=src,
                destination=dst,
                source_name=src_name,
                destination_name=dst_name,
            )

        # 1. Primary shortest route via Dijkstra
        adj = build_adj_from_nx(G)
        shortest_path, shortest_dist = dijkstra(adj, src, dst)

        # 2. Alternative routes via find_alternative_paths
        candidate_paths = find_alternative_paths(G, src, dst, k=max_alternatives + 2)
        
        # Deduplicate and sort candidate routes
        unique_paths = []
        seen = set()
        
        # Always put Dijkstra first
        seen.add(tuple(shortest_path))
        unique_paths.append((shortest_path, shortest_dist))

        for path, dist in candidate_paths:
            t = tuple(path)
            if t not in seen:
                seen.add(t)
                unique_paths.append((path, dist))
                if len(unique_paths) >= max_alternatives + 1:
                    break

        # Build RouteOption objects
        route_options: List[RouteOption] = []
        best_distance = unique_paths[0][1]

        for rank, (path, dist) in enumerate(unique_paths, start=1):
            legs: List[LegDetail] = []
            total_time = 0.0
            full_arc: List[List[float]] = []

            for i in range(len(path) - 1):
                p_from, p_to = path[i], path[i + 1]
                edge_data = G.get_edge_data(p_from, p_to, {})
                leg_dist = float(edge_data.get("distance_km", 0))
                leg_time = float(edge_data.get("travel_time_min", 0) or 0)
                total_time += leg_time

                from_coords = list(get_airport_coordinates(p_from))
                to_coords = list(get_airport_coordinates(p_to))
                leg_arc = calculate_flight_arc(from_coords[0], from_coords[1], to_coords[0], to_coords[1])

                if full_arc:
                    # Avoid duplicate joining points
                    full_arc.extend(leg_arc[1:])
                else:
                    full_arc.extend(leg_arc)

                legs.append(LegDetail(
                    leg_number=i + 1,
                    source=p_from,
                    destination=p_to,
                    source_city=airport_cities.get(p_from, p_from),
                    destination_city=airport_cities.get(p_to, p_to),
                    source_name=airport_names.get(p_from, p_from),
                    destination_name=airport_names.get(p_to, p_to),
                    distance_km=leg_dist,
                    travel_time_min=leg_time,
                    formatted_duration=format_duration(leg_time),
                    start_coords=from_coords,
                    end_coords=to_coords,
                    arc_coordinates=leg_arc,
                ))

            layovers = path[1:-1]
            layover_count = len(layovers)
            is_direct = layover_count == 0

            # Badge naming
            if rank == 1:
                badge = "Optimal Route (Shortest)"
            else:
                diff = dist - best_distance
                badge = f"Option {rank} (+{diff:,.0f} km)"

            route_options.append(RouteOption(
                rank=rank,
                badge=badge,
                path=path,
                path_cities=[airport_cities.get(code, code) for code in path],
                total_distance_km=dist,
                total_travel_time_min=total_time,
                formatted_duration=format_duration(total_time),
                layover_count=layover_count,
                layovers=layovers,
                is_direct=is_direct,
                legs=legs,
                full_arc_coordinates=full_arc,
            ))

        best_route = route_options[0]
        alternatives = route_options[1:]

        return RoutePlanResponse(
            success=True,
            message=f"Found {len(route_options)} route(s) from {src} to {dst}.",
            source=src,
            destination=dst,
            source_name=src_name,
            destination_name=dst_name,
            best_route=best_route,
            alternative_routes=alternatives,
        )


route_service = RouteService()
