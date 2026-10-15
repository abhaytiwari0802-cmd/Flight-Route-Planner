"""Route statistics and chart generation using NumPy, Pandas, Matplotlib, Seaborn and Plotly."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _valid_routes(routes_df):
    df = routes_df.copy()
    if "distance_km" not in df:
        df["distance_km"] = pd.Series(dtype=float)
    df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce")
    df = df.dropna(subset=["distance_km"])
    if "source" not in df:
        df["source"] = ""
    if "destination" not in df:
        df["destination"] = ""
    return df


def route_statistics(routes_df: pd.DataFrame) -> dict:
    distances = _valid_routes(routes_df)["distance_km"].to_numpy(dtype=float)
    if distances.size == 0:
        return {"count": 0}
    return {
        "count": int(distances.size),
        "min": float(np.min(distances)),
        "max": float(np.max(distances)),
        "mean": float(np.mean(distances)),
        "median": float(np.median(distances)),
        "distances": distances,
    }


def plot_distance_bar(routes_df: pd.DataFrame, out: Path = OUTPUT_DIR / "distances_bar.png") -> Path:
    df = _valid_routes(routes_df)
    df["label"] = df["source"].astype(str) + "-" + df["destination"].astype(str)
    df = df.sort_values("distance_km")
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    if df.empty:
        ax.text(.5, .5, "No route data", ha="center", va="center")
    else:
        ax.bar(df["label"], df["distance_km"])
        ax.tick_params(axis="x", labelrotation=90)
    ax.set_ylabel("Distance (km)")
    ax.set_title("Route distances")
    fig.tight_layout(); fig.savefig(out); plt.close(fig)
    return out


def plot_histogram(routes_df: pd.DataFrame, out: Path = OUTPUT_DIR / "distances_hist.png") -> Path:
    distances = _valid_routes(routes_df)["distance_km"].to_numpy(dtype=float)
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    if distances.size:
        ax.hist(distances, bins=min(10, max(1, distances.size)))
    else:
        ax.text(.5, .5, "No route data", ha="center", va="center")
    ax.set_xlabel("Distance (km)"); ax.set_ylabel("Number of routes")
    ax.set_title("Distribution of route distances")
    fig.tight_layout(); fig.savefig(out); plt.close(fig)
    return out


def plot_scatter_distance_time(routes_df: pd.DataFrame, out: Path = OUTPUT_DIR / "distance_time_scatter.png"):
    df = _valid_routes(routes_df)
    df["travel_time_min"] = pd.to_numeric(df.get("travel_time_min"), errors="coerce")
    df = df.dropna(subset=["travel_time_min"])
    if df.empty:
        return None
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.scatterplot(data=df, x="distance_km", y="travel_time_min", hue="source", ax=ax)
    ax.set_xlabel("Distance (km)"); ax.set_ylabel("Estimated travel time (min)")
    ax.set_title("Distance vs Travel Time")
    fig.tight_layout(); fig.savefig(out); plt.close(fig)
    return out


def interactive_bar_plot(routes_df: pd.DataFrame, out: Path = OUTPUT_DIR / "distances_bar.html") -> Path:
    df = _valid_routes(routes_df)
    df["label"] = df["source"].astype(str) + "-" + df["destination"].astype(str)
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    fig = px.bar(df, x="label", y="distance_km", title="Interactive Route Distances")
    fig.write_html(out)
    return out
