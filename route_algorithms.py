"""Dijkstra shortest path and alternative route discovery."""
from typing import Dict, Tuple, List, Optional
import heapq
import math
import networkx as nx


def dijkstra(adj: Dict[str, Dict[str, float]], source: str, target: str) -> Tuple[List[str], float]:
    """Return (path, total weight) using Dijkstra's algorithm.

    Complexity: O((V + E) log V) with a binary heap and adjacency lists.
    All edge weights must be finite and non-negative; zero is allowed by Dijkstra.
    """
    source, target = str(source).strip().upper(), str(target).strip().upper()
    if source == target:
        raise ValueError("Source and destination are the same.")
    if source not in adj or target not in adj:
        raise KeyError("Unknown source or destination code.")
    for node, edges in adj.items():
        for neighbor, weight in edges.items():
            if not math.isfinite(float(weight)) or float(weight) < 0:
                raise ValueError(f"Invalid edge weight for {node} -> {neighbor}.")
    distances = {source: 0.0}
    previous: Dict[str, Optional[str]] = {source: None}
    queue = [(0.0, source)]
    while queue:
        distance, node = heapq.heappop(queue)
        if distance != distances.get(node, math.inf):
            continue
        if node == target:
            break
        for neighbor, weight in adj.get(node, {}).items():
            new_distance = distance + float(weight)
            if new_distance < distances.get(neighbor, math.inf):
                distances[neighbor] = new_distance
                previous[neighbor] = node
                heapq.heappush(queue, (new_distance, neighbor))
    if target not in distances:
        raise nx.NetworkXNoPath(f"No path between {source} and {target}.")
    path, current = [], target
    while current is not None:
        path.append(current)
        current = previous.get(current)
    path.reverse()
    return path, distances[target]


def build_adj_from_nx(G: nx.Graph) -> Dict[str, Dict[str, float]]:
    """Convert an undirected NetworkX graph to a weighted adjacency dictionary."""
    adj = {node: {} for node in G.nodes}
    for u, v, data in G.edges(data=True):
        weight = float(data.get("distance_km", 0))
        adj[u][v] = weight
        adj[v][u] = weight
    return adj


def find_alternative_paths(G: nx.Graph, source: str, target: str, k: int = 3) -> List[Tuple[List[str], float]]:
    """Return up to k distinct simple route candidates without mutating G.

    Uses NetworkX's shortest_simple_paths (Yen-style candidate generation).
    Requires non-negative distance weights and a simple graph.
    """
    source, target = str(source).strip().upper(), str(target).strip().upper()
    if k <= 0:
        return []
    if source not in G or target not in G:
        raise KeyError("Unknown source or destination code.")
    if source == target:
        raise ValueError("Source and destination are the same.")
    if not nx.has_path(G, source, target):
        return []
    candidates = []
    try:
        generator = nx.shortest_simple_paths(G, source, target, weight="distance_km")
        for path in generator:
            length = sum(float(G[u][v].get("distance_km", 0)) for u, v in zip(path, path[1:]))
            candidates.append((path, length))
            if len(candidates) >= k:
                break
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []
    return candidates
