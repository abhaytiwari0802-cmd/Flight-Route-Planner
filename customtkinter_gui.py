"""CustomTkinter dark dashboard for Flight Route Planner.

Graph and persistence are deliberately kept in DataManager/route_algorithms,
so the UI can be connected to another CSV or database without redesigning it.
"""
from __future__ import annotations

import math
import platform
import tkinter as tk
from tkinter import messagebox
from collections import defaultdict

import customtkinter as ctk
import networkx as nx

from .data_manager import DataManager
from .route_algorithms import build_adj_from_nx, dijkstra
from .analytics import route_statistics

# ------------------------------- Theme constants ----------------------------
BG = "#07162B"
PANEL = "#0A1D35"
PANEL_ALT = "#0D2542"
BORDER = "#1B3A5C"
ACTIVE = "#134A7C"
HOVER = "#0F3558"
GREEN = "#00C98D"
GREEN_HOVER = "#00B07B"
BLUE = "#1E90FF"
PURPLE = "#A56BFF"
CYAN = "#19B5E6"
TEXT = "#FFFFFF"
MUTED = "#8FA6C0"
CANVAS_BG = "#061226"
LINE = "#284665"
FONT_FAMILY = "Segoe UI" if platform.system() == "Windows" else "Helvetica"
FONT_TITLE = (FONT_FAMILY, 24, "bold")
FONT_SECTION = (FONT_FAMILY, 13, "bold")
FONT_STAT = (FONT_FAMILY, 26, "bold")
FONT_BODY = (FONT_FAMILY, 10, "normal")
FONT_NAV = (FONT_FAMILY, 11, "normal")
FONT_BUTTON = (FONT_FAMILY, 11, "bold")


def font(size: int, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


class StatCard(ctk.CTkFrame):
    def __init__(self, master, title, value, description, accent, icon, **kwargs):
        super().__init__(master, fg_color=PANEL, border_color=BORDER,
                         border_width=1, corner_radius=8, **kwargs)
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(13, 2))
        ctk.CTkLabel(top, text=icon, width=32, height=30, corner_radius=7,
                     fg_color=PANEL_ALT, text_color=accent,
                     font=font(16, "bold")).pack(side="left")
        ctk.CTkLabel(top, text=title, text_color=accent,
                     font=font(10, "bold")).pack(side="left", padx=9)
        self.value_label = ctk.CTkLabel(self, text=value, text_color=accent,
                                        font=font(26, "bold"))
        self.value_label.pack(anchor="w", padx=14, pady=(1, 0))
        ctk.CTkLabel(self, text=description, text_color=MUTED,
                     font=font(10), anchor="w", wraplength=230).pack(
                         anchor="w", padx=14, pady=(0, 13))

    def set_value(self, value: str):
        self.value_label.configure(text=value)


class Sidebar(ctk.CTkFrame):
    NAV_ITEMS = [
        ("▦", "Dashboard"), ("✈", "Airports"), ("⌁", "Routes"),
        ("⌖", "Shortest Route"), ("⇄", "Alternative Routes"),
        ("◎", "Visualize Network"), ("▥", "Analytics"),
        ("⚙", "Settings"), ("↪", "Exit"),
    ]

    def __init__(self, master, on_navigate):
        super().__init__(master, width=260, corner_radius=0, fg_color=PANEL,
                         border_width=1, border_color=BORDER)
        self.pack_propagate(False)
        self.on_navigate = on_navigate
        self.buttons = {}
        brand = ctk.CTkFrame(self, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(25, 28))
        ctk.CTkLabel(brand, text="✈", text_color=CYAN,
                     font=font(34, "bold")).pack(anchor="w")
        ctk.CTkLabel(brand, text="FLIGHT PLANNER", text_color=TEXT,
                     font=font(15, "bold")).pack(anchor="w", pady=(4, 0))
        ctk.CTkLabel(brand, text="Plan · Explore · Fly", text_color=MUTED,
                     font=font(10)).pack(anchor="w", pady=(4, 0))
        for icon, name in self.NAV_ITEMS:
            btn = ctk.CTkButton(
                self, text=f"  {icon}     {name}", anchor="w", height=39,
                corner_radius=7, fg_color="transparent", hover_color=HOVER,
                text_color=TEXT, font=font(11),
                command=lambda n=name: self.on_navigate(n),
            )
            btn.pack(fill="x", padx=12, pady=3)
            self.buttons[name] = btn
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=20, pady=22)
        ctk.CTkLabel(footer, text="✈  Smarter Routes,\n    Better Connections",
                     justify="left", text_color=CYAN, font=font(10)).pack(anchor="w")
        self.set_active("Dashboard")

    def set_active(self, name):
        for label, button in self.buttons.items():
            button.configure(fg_color=ACTIVE if label == name else "transparent",
                             hover_color=HOVER)


class NetworkCanvas(ctk.CTkFrame):
    """Draws route edges and airport nodes on a native Tk canvas."""
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=PANEL, corner_radius=8,
                         border_width=1, border_color=BORDER, **kwargs)
        self.canvas = tk.Canvas(self, bg=CANVAS_BG, highlightthickness=0,
                                height=260)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        self.graph = nx.Graph()
        self.airports = None
        self.path = []
        self.after(100, self._redraw_if_ready)
        self.canvas.bind("<Configure>", lambda _event: self.draw())

    def set_data(self, graph, airports, path=None):
        self.graph = graph
        self.airports = airports
        self.path = path or []
        self.draw()

    def _redraw_if_ready(self):
        if self.graph:
            self.draw()

    def draw(self):
        if not hasattr(self, "canvas"):
            return
        c = self.canvas
        c.delete("all")
        nodes = list(self.graph.nodes)
        if not nodes:
            c.create_text(25, 35, anchor="nw", text="Add airports and routes to preview your network.",
                          fill=MUTED, font=(FONT_FAMILY, 10))
            return
        width = max(c.winfo_width(), 360)
        height = max(c.winfo_height(), 220)
        # Use a wide, left-to-right grid rather than a vertical/circular layout.
        # This remains readable when the window is resized and avoids a tall graph.
        columns = min(6, max(3, math.ceil(math.sqrt(len(nodes)) * 1.5)))
        rows = math.ceil(len(nodes) / columns)
        left, right = 44, max(44, width - 44)
        top, bottom = 34, max(34, height - 42)
        x_gap = (right - left) / max(1, columns - 1)
        y_gap = (bottom - top) / max(1, rows - 1)
        positions = {}
        for i, node in enumerate(nodes):
            row, col = divmod(i, columns)
            # Stagger alternate rows slightly so labels and edge weights overlap less.
            x = left + col * x_gap + (x_gap * 0.18 if row % 2 else 0)
            positions[node] = (min(width - 30, x), top + row * y_gap)
        path_edges = {frozenset((a, b)) for a, b in zip(self.path, self.path[1:])}
        # Draw other route connections first.
        for a, b, data in self.graph.edges(data=True):
            x1, y1 = positions[a]; x2, y2 = positions[b]
            highlighted = frozenset((a, b)) in path_edges
            color = GREEN if highlighted else LINE
            c.create_line(x1, y1, x2, y2, fill=color,
                          width=3 if highlighted else 1.2,
                          smooth=highlighted, capstyle=tk.ROUND)
            distance = data.get("distance_km", "")
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            c.create_text(mx, my - 7, text=f"{float(distance):,.0f}" if distance != "" else "",
                          fill=GREEN if highlighted else MUTED,
                          font=(FONT_FAMILY, 8, "bold" if highlighted else "normal"))
        start = self.path[0] if self.path else None
        destination = self.path[-1] if self.path else None
        for node, (x, y) in positions.items():
            color = GREEN if node == start else BLUE if node == destination else "#58718F"
            radius = 7 if node in (start, destination) else 5
            c.create_oval(x-radius, y-radius, x+radius, y+radius,
                          fill=color, outline=CANVAS_BG, width=2)
            c.create_text(x, y + 15, text=node, fill=TEXT,
                          font=(FONT_FAMILY, 9, "bold"), anchor="n")


class RouteSearchCard(ctk.CTkFrame):
    def __init__(self, master, airport_codes, on_search):
        super().__init__(master, fg_color=PANEL, corner_radius=8,
                         border_width=1, border_color=BORDER)
        self.on_search = on_search
        ctk.CTkLabel(self, text="Route Search", text_color=TEXT,
                     font=font(13, "bold")).pack(anchor="w", padx=16, pady=(15, 12))
        ctk.CTkLabel(self, text="From", text_color=MUTED, font=font(10)).pack(anchor="w", padx=16)
        self.source = ctk.CTkComboBox(self, values=airport_codes, height=36,
                                      fg_color=CANVAS_BG, border_color=BORDER,
                                      button_color=ACTIVE, button_hover_color=HOVER,
                                      text_color=TEXT, dropdown_fg_color=PANEL_ALT,
                                      dropdown_text_color=TEXT, font=font(10),
                                      dropdown_font=font(10))
        self.source.pack(fill="x", padx=16, pady=(4, 10))
        ctk.CTkLabel(self, text="To", text_color=MUTED, font=font(10)).pack(anchor="w", padx=16)
        self.destination = ctk.CTkComboBox(self, values=airport_codes, height=36,
                                           fg_color=CANVAS_BG, border_color=BORDER,
                                           button_color=ACTIVE, button_hover_color=HOVER,
                                           text_color=TEXT, dropdown_fg_color=PANEL_ALT,
                                           dropdown_text_color=TEXT, font=font(10),
                                           dropdown_font=font(10))
        self.destination.pack(fill="x", padx=16, pady=(4, 13))
        if airport_codes:
            self.source.set(airport_codes[0])
            self.destination.set(airport_codes[1] if len(airport_codes) > 1 else airport_codes[0])
        ctk.CTkButton(self, text="Find Shortest Route", height=38,
                      fg_color=GREEN, hover_color=GREEN_HOVER, text_color=BG,
                      font=font(11, "bold"), command=self._click_search).pack(
                          fill="x", padx=16, pady=(0, 16))

    def _click_search(self):
        self.on_search(self.source.get().strip().upper(), self.destination.get().strip().upper())


class App(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        super().__init__()
        self.title("Flight Route Planner")
        self.geometry("1280x720")
        self.minsize(1100, 650)
        self.configure(fg_color=BG)
        self.dm = DataManager()
        self.graph = nx.Graph()
        self.last_path = []
        self.last_distance = 0.0
        self.last_duration = 0.0
        self._reload_graph()
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = Sidebar(self, self.navigate)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)
        self._build_header()
        self.content = ctk.CTkFrame(self.main, fg_color="transparent")
        self.content.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 8))
        self.status = ctk.CTkLabel(self.main,
            text="Ready  •  Sample routes are simulated, not live aviation data",
            anchor="w", text_color=MUTED, font=font(9), fg_color=PANEL,
            corner_radius=0, height=27)
        self.status.grid(row=2, column=0, sticky="ew")
        self.show_dashboard()

    def _reload_graph(self):
        airports = self.dm.load_airports()
        routes = self.dm.load_routes()
        self.airports_df = airports
        self.routes_df = routes
        self.graph = nx.Graph()
        for row in airports.to_dict("records"):
            self.graph.add_node(row["code"], name=row["name"], city=row["city"])
        for row in routes.to_dict("records"):
            if row.get("source") in self.graph and row.get("destination") in self.graph:
                try:
                    distance = float(row.get("distance_km"))
                except (TypeError, ValueError):
                    continue
                if math.isfinite(distance) and distance >= 0:
                    self.graph.add_edge(row["source"], row["destination"],
                                        distance_km=distance,
                                        travel_time_min=float(row.get("travel_time_min") or 0))

    def _build_header(self):
        header = ctk.CTkFrame(self.main, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 12))
        ctk.CTkLabel(header, text="✈  Welcome to Flight Route Planner",
                     text_color=TEXT, font=font(24, "bold")).pack(anchor="w")
        ctk.CTkLabel(header, text="Plan efficient routes across a simulated airport network.",
                     text_color=MUTED, font=font(10)).pack(anchor="w", pady=(4, 0))

    def _clear_content(self):
        for child in self.content.winfo_children():
            child.destroy()
        # Each page defines its own grid. Reset prior page weights so columns
        # from the dashboard cannot squeeze Alternative Routes or Analytics.
        for index in range(8):
            self.content.grid_columnconfigure(index, weight=0, uniform="")
        for index in range(8):
            self.content.grid_rowconfigure(index, weight=0, uniform="")

    def navigate(self, page):
        if page == "Exit":
            self.destroy(); return
        self.sidebar.set_active(page)
        if page in ("Dashboard", "Shortest Route"):
            self.show_dashboard()
        elif page == "Airports":
            self.show_table_page("Airports", self.airports_df, ["code", "name", "city"])
        elif page == "Routes":
            self.show_table_page("Routes", self.routes_df,
                                 ["source", "destination", "distance_km", "travel_time_min"])
        elif page == "Alternative Routes":
            self.show_alternatives()
        elif page == "Visualize Network":
            self.show_network_page()
        elif page == "Analytics":
            self.show_analytics_page()
        elif page == "Settings":
            self.show_settings_page()

    def show_dashboard(self):
        self._reload_graph()
        self._clear_content()
        self.content.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stats")
        stats = route_statistics(self.routes_df)
        metrics = [
            ("Airports", str(len(self.airports_df)), "Airports in network", BLUE, "✈"),
            ("Routes", str(len(self.routes_df)), "Connections available", GREEN, "⌁"),
            ("Shortest Leg", f"{stats.get('min', 0):,.0f} km" if stats.get("count") else "—", "Minimum route distance", PURPLE, "⌖"),
            ("Average Leg", f"{stats.get('mean', 0):,.0f} km" if stats.get("count") else "—", "Average route distance", CYAN, "▥"),
        ]
        for col, metric in enumerate(metrics):
            card = StatCard(self.content, *metric)
            card.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 8, 0), pady=(0, 12))
        self.content.grid_rowconfigure(1, weight=1)
        body = ctk.CTkFrame(self.content, fg_color="transparent")
        body.grid(row=1, column=0, columnspan=4, sticky="nsew")
        body.grid_columnconfigure(0, weight=4, uniform="body")
        body.grid_columnconfigure(1, weight=6, uniform="body")
        body.grid_rowconfigure(1, weight=1)
        self.search_card = RouteSearchCard(body, list(self.graph.nodes), self.find_route)
        self.search_card.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))
        overview = ctk.CTkFrame(body, fg_color=PANEL, corner_radius=8,
                                 border_width=1, border_color=BORDER)
        overview.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(0, 3))
        ctk.CTkLabel(overview, text="Route Overview", text_color=TEXT,
                     font=font(13, "bold")).pack(anchor="w", padx=15, pady=(14, 8))
        self.result_label = ctk.CTkLabel(overview, text="Choose two airports to find a route.",
                                         text_color=MUTED, font=font(10), wraplength=350,
                                         justify="left")
        self.result_label.pack(anchor="w", padx=15, pady=(0, 12))
        mini = ctk.CTkFrame(overview, fg_color="transparent")
        mini.pack(fill="x", padx=12, pady=(0, 12))
        mini.grid_columnconfigure((0, 1), weight=1)
        self.distance_label = self._mini_stat(mini, 0, "Total Distance", "—", GREEN)
        self.duration_label = self._mini_stat(mini, 1, "Estimated Duration", "—", CYAN)
        network_card = ctk.CTkFrame(body, fg_color=PANEL, corner_radius=8,
                                    border_width=1, border_color=BORDER)
        network_card.grid(row=0, column=1, rowspan=2, sticky="nsew", pady=(0, 3))
        top = ctk.CTkFrame(network_card, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(13, 5))
        ctk.CTkLabel(top, text="Network Snapshot", text_color=TEXT,
                     font=font(13, "bold")).pack(side="left")
        ctk.CTkLabel(top, text=f"{self.graph.number_of_nodes()} airports · {self.graph.number_of_edges()} routes",
                     text_color=MUTED, font=font(9)).pack(side="right")
        self.network_canvas = NetworkCanvas(network_card)
        self.network_canvas.pack(fill="both", expand=True, padx=10, pady=(4, 8))
        legend = ctk.CTkFrame(network_card, fg_color="transparent")
        legend.pack(fill="x", padx=12, pady=(0, 12))
        for label, color in (("Start", GREEN), ("Destination", BLUE), ("Shortest route", GREEN), ("Other routes", LINE)):
            ctk.CTkLabel(legend, text=f"●  {label}", text_color=color,
                         font=font(9)).pack(side="left", padx=(0, 11))
        self.network_canvas.set_data(self.graph, self.airports_df, self.last_path)
        bottom = ctk.CTkFrame(self.content, fg_color="transparent")
        bottom.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        bottom.grid_columnconfigure((0, 1), weight=1, uniform="bottom")
        self.popular_card = ctk.CTkFrame(bottom, fg_color=PANEL, corner_radius=8,
                                         border_width=1, border_color=BORDER)
        self.popular_card.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.distribution_card = ctk.CTkFrame(bottom, fg_color=PANEL, corner_radius=8,
                                              border_width=1, border_color=BORDER)
        self.distribution_card.grid(row=0, column=1, sticky="ew")
        self._draw_popular_connections()
        self._draw_distribution()

    def _mini_stat(self, parent, column, title, value, accent):
        box = ctk.CTkFrame(parent, fg_color=PANEL_ALT, corner_radius=7)
        box.grid(row=0, column=column, sticky="ew", padx=3)
        ctk.CTkLabel(box, text=title, text_color=MUTED, font=font(9)).pack(anchor="w", padx=10, pady=(8, 1))
        value_label = ctk.CTkLabel(box, text=value, text_color=accent, font=font(16, "bold"))
        value_label.pack(anchor="w", padx=10, pady=(0, 8))
        return value_label

    def find_route(self, source, target):
        if source == target:
            messagebox.showwarning("Choose different airports", "Starting and destination airports must be different.", parent=self)
            self.status.configure(text="Please choose two different airports.")
            return
        try:
            path, distance = dijkstra(build_adj_from_nx(self.graph), source, target)
        except (ValueError, KeyError, nx.NetworkXNoPath) as exc:
            messagebox.showerror("Route unavailable", str(exc), parent=self)
            self.status.configure(text="No route found for the selected airports.")
            return
        self.last_path = path
        self.last_distance = distance
        duration = 0.0
        for a, b in zip(path, path[1:]):
            duration += float(self.graph[a][b].get("travel_time_min", 0) or 0)
        self.last_duration = duration
        self.result_label.configure(text="  →  ".join(path), text_color=TEXT)
        self.distance_label.configure(text=f"{distance:,.0f} km")
        self.duration_label.configure(text=self._format_duration(duration))
        self.network_canvas.set_data(self.graph, self.airports_df, path)
        self.status.configure(text=f"Shortest route found: {' → '.join(path)}  •  {distance:,.0f} km")

    @staticmethod
    def _format_duration(minutes):
        if not minutes:
            return "—"
        hours, mins = divmod(int(round(minutes)), 60)
        return f"{hours}h {mins}m" if hours else f"{mins} min"

    def _draw_popular_connections(self):
        card = self.popular_card
        ctk.CTkLabel(card, text="Popular Connections", text_color=TEXT,
                     font=font(13, "bold")).pack(anchor="w", padx=14, pady=(10, 4))
        canvas = tk.Canvas(card, height=92, bg=PANEL, highlightthickness=0)
        canvas.pack(fill="x", padx=10, pady=(0, 8))
        edges = sorted(self.graph.edges(data=True), key=lambda e: float(e[2].get("distance_km", 0)))[:4]
        max_distance = max((float(e[2].get("distance_km", 0)) for e in edges), default=1) or 1
        canvas.bind("<Configure>", lambda _e: self._render_popular(canvas, edges, max_distance))
        self._render_popular(canvas, edges, max_distance)

    def _render_popular(self, canvas, edges, max_distance):
        canvas.delete("all")
        width = max(canvas.winfo_width(), 350)
        for i, (a, b, data) in enumerate(edges):
            y = 12 + i * 20
            distance = float(data.get("distance_km", 0))
            canvas.create_text(2, y, anchor="w", text=f"{a} – {b}", fill=MUTED, font=(FONT_FAMILY, 8))
            x0, x1 = 85, width - 45
            canvas.create_rectangle(x0, y-4, x1, y+4, fill=CANVAS_BG, outline="")
            canvas.create_rectangle(x0, y-4, x0+(x1-x0)*distance/max_distance, y+4,
                                    fill=GREEN if i % 2 == 0 else BLUE, outline="")
            canvas.create_text(width-2, y, anchor="e", text=f"{distance:,.0f}", fill=TEXT, font=(FONT_FAMILY, 8))

    def _draw_distribution(self):
        card = self.distribution_card
        ctk.CTkLabel(card, text="Distance Distribution", text_color=TEXT,
                     font=font(13, "bold")).pack(anchor="w", padx=14, pady=(10, 4))
        canvas = tk.Canvas(card, height=92, bg=PANEL, highlightthickness=0)
        canvas.pack(fill="x", padx=10, pady=(0, 8))
        distances = [float(d) for d in self.routes_df["distance_km"].dropna().tolist()]
        if not distances:
            canvas.create_text(10, 20, anchor="w", text="No route distance data", fill=MUTED, font=(FONT_FAMILY, 9))
            return
        bins = min(6, max(1, len(distances)))
        low, high = min(distances), max(distances)
        if low == high:
            counts = [len(distances)]
        else:
            step = (high-low)/bins
            counts = [0] * bins
            for value in distances:
                counts[min(bins-1, int((value-low)/step))] += 1
        canvas.bind("<Configure>", lambda _e: self._render_histogram(canvas, counts))
        self._render_histogram(canvas, counts)

    def _render_histogram(self, canvas, counts):
        canvas.delete("all")
        width, height = max(canvas.winfo_width(), 320), max(canvas.winfo_height(), 85)
        max_count = max(counts, default=1) or 1
        gap = 7
        bar_width = max(12, (width-25-gap*(len(counts)-1)) / max(1, len(counts)))
        for i, count in enumerate(counts):
            x0 = 12 + i*(bar_width+gap); x1=x0+bar_width
            bar_height = max(2, (height-28)*count/max_count)
            canvas.create_rectangle(x0, height-18-bar_height, x1, height-18,
                                    fill=BLUE, outline="")
            canvas.create_text((x0+x1)/2, height-18-bar_height-7, text=str(count),
                               fill=MUTED, font=(FONT_FAMILY, 8))

    def show_table_page(self, title, dataframe, columns):
        self._clear_content()
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self.content, text=title, text_color=TEXT, font=font(18, "bold")).grid(
            row=0, column=0, sticky="w", pady=(2, 12))
        table = ctk.CTkScrollableFrame(self.content, fg_color=PANEL, corner_radius=8,
                                       border_width=1, border_color=BORDER)
        table.grid(row=1, column=0, sticky="nsew")
        for col, name in enumerate(columns):
            ctk.CTkLabel(table, text=name.replace("_", " ").title(), text_color=CYAN,
                         font=font(10, "bold"), anchor="w").grid(row=0, column=col, sticky="ew", padx=12, pady=10)
            table.grid_columnconfigure(col, weight=1)
        for row_index, row in enumerate(dataframe[columns].to_dict("records"), start=1):
            for col, name in enumerate(columns):
                value = row.get(name, "")
                if isinstance(value, float): value = f"{value:,.1f}"
                ctk.CTkLabel(table, text=str(value), text_color=TEXT if row_index % 2 else MUTED,
                             font=font(10), anchor="w").grid(row=row_index, column=col, sticky="ew", padx=12, pady=8)

    def show_alternatives(self):
        self._clear_content()
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(self.content, text="Alternative Routes", text_color=TEXT,
                     font=font(18, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 12))

        panel = ctk.CTkFrame(self.content, fg_color=PANEL, corner_radius=8,
                             border_width=1, border_color=BORDER)
        panel.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        panel.grid_columnconfigure((0, 1), weight=1, uniform="route-pickers")
        codes = sorted(self.graph.nodes)
        if len(codes) < 2:
            ctk.CTkLabel(panel, text="Add at least two airports to compare routes.",
                         text_color=MUTED, font=font(10)).grid(row=0, column=0, padx=16, pady=20)
            return

        ctk.CTkLabel(panel, text="Starting airport", text_color=MUTED,
                     font=font(10)).grid(row=0, column=0, sticky="w", padx=(16, 8), pady=(14, 4))
        ctk.CTkLabel(panel, text="Destination airport", text_color=MUTED,
                     font=font(10)).grid(row=0, column=1, sticky="w", padx=(8, 16), pady=(14, 4))
        source = ctk.CTkComboBox(panel, values=codes, font=font(10), height=36,
                                 fg_color=CANVAS_BG, border_color=BORDER,
                                 button_color=ACTIVE, button_hover_color=HOVER,
                                 dropdown_fg_color=PANEL_ALT, dropdown_text_color=TEXT)
        source.set("JFK" if "JFK" in codes else codes[0])
        source.grid(row=1, column=0, sticky="ew", padx=(16, 8), pady=(0, 12))
        target = ctk.CTkComboBox(panel, values=codes, font=font(10), height=36,
                                 fg_color=CANVAS_BG, border_color=BORDER,
                                 button_color=ACTIVE, button_hover_color=HOVER,
                                 dropdown_fg_color=PANEL_ALT, dropdown_text_color=TEXT)
        target.set("LAX" if "LAX" in codes else codes[1])
        target.grid(row=1, column=1, sticky="ew", padx=(8, 16), pady=(0, 12))
        output = ctk.CTkFrame(self.content, fg_color="transparent")
        output.grid(row=2, column=0, sticky="nsew")
        output.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(output, text="Available route options", text_color=TEXT,
                     font=font(13, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 8))
        results = ctk.CTkScrollableFrame(output, fg_color="transparent", corner_radius=8)
        results.grid(row=1, column=0, sticky="nsew")
        output.grid_rowconfigure(1, weight=1)

        def compare():
            a, b = source.get().strip().upper(), target.get().strip().upper()
            if a == b:
                messagebox.showwarning("Invalid selection", "Choose two different airports.", parent=self)
                return
            for child in results.winfo_children():
                child.destroy()
            if a not in self.graph or b not in self.graph:
                ctk.CTkLabel(results, text="Select airports from the dropdown lists.",
                             text_color=MUTED, font=font(10)).pack(anchor="w", padx=12, pady=12)
                return
            try:
                paths = nx.shortest_simple_paths(self.graph, a, b, weight="distance_km")
                found = 0
                for index, path in enumerate(paths):
                    distance = sum(float(self.graph[x][y].get("distance_km", 0))
                                   for x, y in zip(path, path[1:]))
                    duration = sum(float(self.graph[x][y].get("travel_time_min", 0) or 0)
                                   for x, y in zip(path, path[1:]))
                    card = ctk.CTkFrame(results, fg_color=PANEL, corner_radius=8,
                                        border_width=1, border_color=BORDER)
                    card.pack(fill="x", pady=5)
                    ctk.CTkLabel(card, text=f"ROUTE {index + 1}", text_color=GREEN if index == 0 else CYAN,
                                 font=font(10, "bold")).pack(anchor="w", padx=14, pady=(10, 3))
                    ctk.CTkLabel(card, text="  →  ".join(path), text_color=TEXT,
                                 font=font(12, "bold"), wraplength=900, justify="left").pack(
                                     anchor="w", padx=14, pady=(0, 5))
                    ctk.CTkLabel(card, text=f"Distance: {distance:,.0f} km     •     Estimated duration: {self._format_duration(duration)}",
                                 text_color=MUTED, font=font(10)).pack(anchor="w", padx=14, pady=(0, 10))
                    found += 1
                    if found >= 5:
                        break
                if not found:
                    ctk.CTkLabel(results, text="No route found between these airports.",
                                 text_color=MUTED, font=font(10)).pack(anchor="w", padx=12, pady=12)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                ctk.CTkLabel(results, text="No route found between these airports.",
                             text_color=MUTED, font=font(10)).pack(anchor="w", padx=12, pady=12)

        ctk.CTkButton(panel, text="Compare Alternative Routes", height=38,
                      fg_color=GREEN, hover_color=GREEN_HOVER, text_color=BG,
                      font=font(11, "bold"), command=compare).grid(
                          row=2, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 16))
        # Populate useful results immediately, so the page is not blank on entry.
        compare()

    def show_network_page(self):
        self._clear_content()
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self.content, text="Visualize Network", text_color=TEXT,
                     font=font(18, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 12))
        panel = NetworkCanvas(self.content)
        panel.grid(row=1, column=0, sticky="nsew")
        panel.set_data(self.graph, self.airports_df, self.last_path)

    def show_analytics_page(self):
        self._clear_content()
        self.content.grid_columnconfigure((0, 1), weight=1, uniform="analytics")
        self.content.grid_rowconfigure(1, weight=1)
        stats = route_statistics(self.routes_df)
        values = [
            ("Total routes", str(len(self.routes_df)), BLUE),
            ("Shortest leg", f"{stats.get('min', 0):,.0f} km" if stats.get("count") else "—", GREEN),
            ("Longest leg", f"{stats.get('max', 0):,.0f} km" if stats.get("count") else "—", PURPLE),
            ("Average leg", f"{stats.get('mean', 0):,.0f} km" if stats.get("count") else "—", CYAN),
        ]
        stats_row = ctk.CTkFrame(self.content, fg_color="transparent")
        stats_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        stats_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="analytics-stats")
        for i, (title, value, color) in enumerate(values):
            card = StatCard(stats_row, title, value, "Calculated from route data", color, "▥")
            card.grid(row=0, column=i, sticky="ew", padx=5)

        popular = ctk.CTkFrame(self.content, fg_color=PANEL, corner_radius=8,
                               border_width=1, border_color=BORDER)
        popular.grid(row=1, column=0, sticky="nsew", padx=(0, 7), pady=(0, 8))
        distribution = ctk.CTkFrame(self.content, fg_color=PANEL, corner_radius=8,
                                    border_width=1, border_color=BORDER)
        distribution.grid(row=1, column=1, sticky="nsew", padx=(7, 0), pady=(0, 8))
        ctk.CTkLabel(popular, text="Routes by Airport", text_color=TEXT,
                     font=font(13, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
        degree_canvas = tk.Canvas(popular, bg=PANEL, highlightthickness=0, height=280)
        degree_canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        ctk.CTkLabel(distribution, text="Distance Distribution", text_color=TEXT,
                     font=font(13, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
        distance_canvas = tk.Canvas(distribution, bg=PANEL, highlightthickness=0, height=280)
        distance_canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        degrees = sorted(self.graph.degree, key=lambda item: (-item[1], item[0]))[:8]
        distances = [float(v) for v in self.routes_df["distance_km"].dropna().tolist()]
        bins = 6
        if distances:
            low, high = min(distances), max(distances)
            counts = [0] * bins
            if low == high:
                counts[0] = len(distances)
            else:
                step = (high - low) / bins
                for value in distances:
                    counts[min(bins - 1, int((value - low) / step))] += 1
        else:
            low, high, counts = 0, 0, []

        def draw_degrees(_event=None):
            degree_canvas.delete("all")
            width = max(degree_canvas.winfo_width(), 300)
            bar_left, bar_right = 72, width - 34
            max_degree = max((degree for _, degree in degrees), default=1) or 1
            for i, (code, degree) in enumerate(degrees):
                y = 25 + i * 30
                degree_canvas.create_text(4, y, anchor="w", text=code, fill=MUTED,
                                          font=(FONT_FAMILY, 9, "bold"))
                degree_canvas.create_rectangle(bar_left, y - 7, bar_right, y + 7,
                                               fill=CANVAS_BG, outline="")
                degree_canvas.create_rectangle(bar_left, y - 7,
                    bar_left + (bar_right - bar_left) * degree / max_degree, y + 7,
                    fill=GREEN if i == 0 else BLUE, outline="")
                degree_canvas.create_text(bar_right + 5, y, anchor="w", text=str(degree),
                                          fill=TEXT, font=(FONT_FAMILY, 9))

        def draw_dist(_event=None):
            distance_canvas.delete("all")
            width = max(distance_canvas.winfo_width(), 300)
            height = max(distance_canvas.winfo_height(), 220)
            if not counts:
                distance_canvas.create_text(15, 20, anchor="nw", text="No distance data available.",
                                            fill=MUTED, font=(FONT_FAMILY, 10))
                return
            max_count = max(counts) or 1
            gap = 10
            plot_left, plot_right = 24, width - 16
            slot = (plot_right - plot_left) / len(counts)
            for i, count in enumerate(counts):
                x0 = plot_left + i * slot + gap / 2
                x1 = plot_left + (i + 1) * slot - gap / 2
                bar_height = (height - 65) * count / max_count
                y0, y1 = height - 35 - bar_height, height - 35
                distance_canvas.create_rectangle(x0, y0, x1, y1, fill=BLUE, outline="")
                distance_canvas.create_text((x0 + x1) / 2, y0 - 10, text=str(count),
                                            fill=TEXT, font=(FONT_FAMILY, 9, "bold"))
                label = f"{low + (high-low)*i/bins:,.0f}"
                distance_canvas.create_text((x0 + x1) / 2, height - 18, text=label,
                                            fill=MUTED, font=(FONT_FAMILY, 8))
            distance_canvas.create_text(width - 12, height - 3, anchor="se", text="km",
                                        fill=MUTED, font=(FONT_FAMILY, 8))

        degree_canvas.bind("<Configure>", draw_degrees)
        distance_canvas.bind("<Configure>", draw_dist)
        self.after(80, draw_degrees)
        self.after(80, draw_dist)

    def show_settings_page(self):
        self._clear_content()
        ctk.CTkLabel(self.content, text="Settings", text_color=TEXT, font=font(18, "bold")).pack(anchor="w", pady=(0, 12))
        panel = ctk.CTkFrame(self.content, fg_color=PANEL, corner_radius=8, border_width=1, border_color=BORDER)
        panel.pack(fill="x")
        ctk.CTkLabel(panel, text="Appearance", text_color=TEXT, font=font(13, "bold")).pack(anchor="w", padx=16, pady=(16, 5))
        ctk.CTkLabel(panel, text="Dark mode is enabled for this Flight Route Planner app.", text_color=MUTED, font=font(10)).pack(anchor="w", padx=16, pady=(0, 16))


if __name__ == "__main__":
    App().mainloop()
