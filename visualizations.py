"""Network visualization helpers."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def draw_network(G: nx.Graph, highlight_path=None, out: Path = OUTPUT_DIR / "network.png") -> Path:
    """Save the network plot, highlighting a selected path when supplied."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 7), facecolor="#F4F7F5")
    ax.set_facecolor("#F4F7F5")
    if G.number_of_nodes() == 0:
        ax.text(0.5, 0.5, "No airport data available", ha="center", va="center", color="#26352B")
        ax.axis("off")
        fig.savefig(out, bbox_inches="tight")
        plt.close(fig)
        return out
    pos = nx.spring_layout(G, seed=42)
    nx.draw_networkx_nodes(G, pos, node_color="#168BFF", edgecolors="#26352B", linewidths=1.5, node_size=650, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=8, font_color="#26352B", font_family="DejaVu Sans", ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color="#C7D2CB", width=1.8, ax=ax)
    labels = {(u, v): f"{data.get('distance_km', 0):g} km"
              for u, v, data in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels, font_size=7, font_color="#64756A", ax=ax)
    if highlight_path and len(highlight_path) > 1:
        path_edges = list(zip(highlight_path, highlight_path[1:]))
        nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color="#14A04B", width=3.5, ax=ax)
    ax.set_title("Airport Network (simulated data)", color="#26352B", fontsize=14, fontweight="bold")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out
