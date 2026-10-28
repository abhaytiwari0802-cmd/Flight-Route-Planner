import pandas as pd
import pytest
from src.data_manager import DataManager
from src.models import Airport, FlightRoute


def test_add_airport_and_duplicate_rejected(tmp_path):
    dm = DataManager(tmp_path / "airports.csv", tmp_path / "routes.csv")
    dm.add_airport(Airport(" tst ", "Test Airport", "Test City"))
    assert dm.load_airports().iloc[0]["code"] == "TST"
    with pytest.raises(ValueError):
        dm.add_airport(Airport("TST", "Duplicate", "City"))


def test_add_and_delete_route(tmp_path):
    dm = DataManager(tmp_path / "airports.csv", tmp_path / "routes.csv")
    dm.add_airport(Airport("A1", "Airport 1", "City 1"))
    dm.add_airport(Airport("A2", "Airport 2", "City 2"))
    dm.add_route(FlightRoute("A1", "A2", 123.4, 90))
    assert len(dm.load_routes()) == 1
    with pytest.raises(ValueError):
        dm.add_route(FlightRoute("A2", "A1", 123.4, 90))
    dm.delete_route(0)
    assert dm.load_routes().empty


def test_delete_airport_removes_connected_routes(tmp_path):
    dm = DataManager(tmp_path / "airports.csv", tmp_path / "routes.csv")
    for code in ["A1", "A2", "A3"]:
        dm.add_airport(Airport(code, code, "City"))
    dm.add_route(FlightRoute("A1", "A2", 10))
    dm.add_route(FlightRoute("A2", "A3", 20))
    dm.delete_airport("A2")
    assert set(dm.load_airports()["code"]) == {"A1", "A3"}
    assert dm.load_routes().empty


def test_invalid_route_distance():
    with pytest.raises(ValueError):
        FlightRoute("A1", "A2", 0)
    with pytest.raises(ValueError):
        FlightRoute("A1", "A2", float("nan"))


def test_pandas_2_compatible_add_operations(tmp_path):
    dm = DataManager(tmp_path / "airports.csv", tmp_path / "routes.csv")
    dm.add_airport(Airport("A1", "Airport 1", "City 1"))
    dm.add_airport(Airport("A2", "Airport 2", "City 2"))
    dm.add_route(FlightRoute("A1", "A2", 100))
    assert len(dm.load_airports()) == 2
    assert len(dm.load_routes()) == 1
