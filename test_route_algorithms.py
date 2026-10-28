import pytest
import networkx as nx
from src.route_algorithms import dijkstra, build_adj_from_nx, find_alternative_paths


def test_dijkstra_direct_route():
    path, distance = dijkstra({"A": {"B": 100}, "B": {"A": 100}}, "A", "B")
    assert path == ["A", "B"]
    assert distance == 100


def test_dijkstra_via_intermediate():
    adj = {"A": {"B": 50, "C": 300}, "B": {"A": 50, "C": 50}, "C": {"A": 300, "B": 50}}
    path, distance = dijkstra(adj, "A", "C")
    assert path == ["A", "B", "C"]
    assert distance == 100


def test_dijkstra_no_path():
    with pytest.raises(nx.NetworkXNoPath):
        dijkstra({"A": {}, "B": {}}, "A", "B")


def test_dijkstra_invalid_source_and_same_source():
    with pytest.raises(KeyError):
        dijkstra({"A": {}}, "A", "Z")
    with pytest.raises(ValueError):
        dijkstra({"A": {}}, "A", "A")


def test_dijkstra_rejects_negative_weight():
    with pytest.raises(ValueError):
        dijkstra({"A": {"B": -1}, "B": {}}, "A", "B")


def test_alternative_paths_does_not_mutate_graph():
    graph = nx.Graph()
    graph.add_weighted_edges_from([
        ("A", "B", 2), ("B", "D", 2), ("A", "C", 3), ("C", "D", 3), ("A", "D", 10)
    ], weight="distance_km")
    before = sorted((u, v, d["distance_km"]) for u, v, d in graph.edges(data=True))
    paths = find_alternative_paths(graph, "A", "D", 3)
    after = sorted((u, v, d["distance_km"]) for u, v, d in graph.edges(data=True))
    assert len(paths) == 3
    assert before == after
    assert paths[0][0] == ["A", "B", "D"]
    assert paths[0][1] == 4
