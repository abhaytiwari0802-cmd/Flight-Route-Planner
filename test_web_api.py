"""Integration and unit tests for FastAPI routers, services, and CSV operations."""
import pytest
from web.routers.airports import (
    get_all_airports,
    search_airports,
    get_airport,
    create_airport,
    update_airport,
    delete_airport,
)
from web.routers.routes import (
    get_all_routes,
    create_route,
    update_route,
    delete_route,
)
from web.routers.planner import plan_route, get_network_graph
from web.routers.analytics import get_analytics
from web.models import (
    AirportCreate,
    AirportUpdate,
    RouteCreate,
    RouteUpdate,
    RoutePlanRequest,
)


def test_get_all_airports():
    airports = get_all_airports()
    assert len(airports) >= 15
    codes = [a["code"] for a in airports]
    assert "JFK" in codes
    assert "LAX" in codes
    assert "ORD" in codes


def test_search_airports():
    results = search_airports(q="New")
    assert len(results) > 0
    assert any("New" in a["city"] or "New" in a["name"] for a in results)


def test_get_airport_details():
    airport = get_airport("JFK")
    assert airport["code"] == "JFK"
    assert "New York" in airport["city"]
    assert airport["lat"] > 0 and airport["lon"] < 0
    assert airport["routes_count"] > 0


def test_get_all_routes():
    routes = get_all_routes()
    assert len(routes) >= 20
    first = routes[0]
    assert "source" in first and "destination" in first
    assert first["distance_km"] > 0
    assert len(first["source_coords"]) == 2


def test_plan_route_shortest():
    req = RoutePlanRequest(source="JFK", destination="LAX")
    res = plan_route(req)
    assert res.success is True
    assert res.best_route is not None
    assert res.best_route.path[0] == "JFK"
    assert res.best_route.path[-1] == "LAX"
    assert res.best_route.total_distance_km == 3983.0
    assert res.best_route.is_direct is True


def test_plan_route_multi_leg():
    req = RoutePlanRequest(source="JFK", destination="SFO")
    res = plan_route(req)
    assert res.success is True
    assert res.best_route is not None
    assert res.best_route.path[0] == "JFK"
    assert res.best_route.path[-1] == "SFO"
    assert res.best_route.layover_count >= 1
    assert len(res.best_route.legs) >= 2
    assert len(res.best_route.full_arc_coordinates) > 0
    assert len(res.alternative_routes) > 0


def test_network_topology():
    net = get_network_graph()
    assert net["total_nodes"] >= 15
    assert net["total_edges"] >= 20
    assert len(net["nodes"]) == net["total_nodes"]
    assert len(net["edges"]) == net["total_edges"]


def test_analytics_metrics():
    analytics = get_analytics()
    assert analytics.total_airports >= 15
    assert analytics.total_routes >= 20
    assert analytics.shortest_leg_km > 0
    assert analytics.longest_leg_km > analytics.shortest_leg_km
    assert len(analytics.busiest_airports) > 0
    assert len(analytics.distance_distribution["counts"]) == 6
    assert len(analytics.scatter_data) > 0


def test_airport_crud():
    # 1. Create airport ZZZ
    create_payload = AirportCreate(code="ZZZ", name="Temp Test Airport", city="Temp City")
    created = create_airport(create_payload)
    assert created["code"] == "ZZZ"

    # 2. Update airport ZZZ
    update_payload = AirportUpdate(name="Updated Temp Name", city="Updated City")
    updated = update_airport("ZZZ", update_payload)
    assert updated["name"] == "Updated Temp Name"

    # 3. Delete airport ZZZ
    deleted = delete_airport("ZZZ")
    assert deleted["success"] is True


def test_route_crud():
    # 1. Add route between two existing airports
    create_payload = RouteCreate(source="JFK", destination="MIA", distance_km=1750.0, travel_time_min=180.0)
    # Check if JFK-MIA exists or use a pair without direct connection
    routes = get_all_routes()
    existing_pairs = {(r["source"], r["destination"]) for r in routes}
    existing_pairs.update({(r["destination"], r["source"]) for r in routes})

    src, dst = "PDX", "BOS"
    if (src, dst) not in existing_pairs:
        route_create = RouteCreate(source=src, destination=dst, distance_km=4100.0, travel_time_min=320.0)
        new_route = create_route(route_create)
        assert new_route["source"] == src
        assert new_route["destination"] == dst

        # Update it
        idx = new_route["index"]
        update_route(idx, RouteUpdate(distance_km=4150.0))

        # Delete it
        del_res = delete_route(idx)
        assert del_res["success"] is True
