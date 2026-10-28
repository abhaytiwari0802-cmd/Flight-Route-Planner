"""Build an undirected weighted airport network."""
import networkx as nx
import pandas as pd


class GraphManager:
    def __init__(self, airports_df: pd.DataFrame, routes_df: pd.DataFrame):
        self.airports_df = airports_df
        self.routes_df = routes_df
        self.G = nx.Graph()
        self.build_graph()

    def build_graph(self):
        self.G.clear()
        for _, row in self.airports_df.iterrows():
            self.G.add_node(
                str(row["code"]).strip().upper(),
                name=row.get("name", ""),
                city=row.get("city", ""),
            )
        for _, row in self.routes_df.iterrows():
            source = str(row.get("source", "")).strip().upper()
            destination = str(row.get("destination", "")).strip().upper()
            try:
                distance = float(row["distance_km"])
            except (TypeError, ValueError, KeyError):
                continue
            if source not in self.G or destination not in self.G:
                continue
            if source == destination or distance <= 0:
                continue
            attrs = {"distance_km": distance}
            try:
                time = float(row.get("travel_time_min", ""))
                if time > 0:
                    attrs["travel_time_min"] = time
            except (TypeError, ValueError):
                pass
            self.G.add_edge(source, destination, **attrs)

    def nodes(self):
        return list(self.G.nodes)

    def edges(self):
        return list(self.G.edges(data=True))

    def to_networkx(self):
        return self.G
