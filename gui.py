"""Tkinter desktop interface for the Flight Route Planner."""
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import networkx as nx
from .data_manager import DataManager
from .models import Airport, FlightRoute
from .graph_manager import GraphManager
from .route_algorithms import build_adj_from_nx, dijkstra, find_alternative_paths
from .analytics import route_statistics


class FlightPlannerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Flight Route Planner")
        self.root.geometry("1450x900")
        self.root.minsize(1120, 720)
        self.dm = DataManager()
        self._build_ui()

    def _build_ui(self):
        """Build a modern, card-based desktop interface."""
        self.root.configure(bg="#F4F7F5")
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#F4F7F5")
        style.configure("TLabel", background="#F4F7F5", foreground="#26352B", font=("Segoe UI", 10))
        style.configure("PageTitle.TLabel", font=("Segoe UI", 23, "bold"), foreground="#26352B")
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10), foreground="#64756A")
        style.configure("Card.TLabelframe", background="#FFFFFF", bordercolor="#DDE8E0", relief="solid")
        style.configure("Card.TLabelframe.Label", background="#FFFFFF", foreground="#26352B", font=("Segoe UI", 11, "bold"))
        style.configure("Treeview", background="#FFFFFF", fieldbackground="#FFFFFF", foreground="#26352B", rowheight=32, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#EAF3ED", foreground="#26352B", font=("Segoe UI", 10, "bold"), padding=8)
        style.map("Treeview", background=[("selected", "#D9F0E1")], foreground=[("selected", "#26352B")])
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 7), background="#EAF3ED", foreground="#26352B")
        style.map("TButton", background=[("active", "#D9F0E1")])
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 9), background="#14A04B", foreground="#E8F6ED")
        style.map("Accent.TButton", background=[("active", "#11833D")], foreground=[("active", "#E8F6ED")])

        # Shared airport selector styling: clean web-like typography and dark dropdown list.
        style.configure(
            "Airport.TCombobox",
            font=("Segoe UI", 11),
            padding=(10, 9),
            fieldbackground="#FFFFFF",
            background="#FFFFFF",
            foreground="#26352B",
            arrowcolor="#14A04B",
            bordercolor="#BBDCC7",
            lightcolor="#BBDCC7",
            darkcolor="#BBDCC7",
            insertcolor="#26352B",
        )
        style.map(
            "Airport.TCombobox",
            fieldbackground=[("readonly", "#FFFFFF"), ("focus", "#103553")],
            foreground=[("readonly", "#26352B")],
            selectbackground=[("readonly", "#FFFFFF")],
            selectforeground=[("readonly", "#26352B")],
            bordercolor=[("focus", "#14A04B"), ("active", "#14A04B")],
        )
        # Tk uses a separate classic Listbox for the popup on many Windows builds;
        # option_add styles the actual opened menu, not just the closed selector.
        self.root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 11))
        self.root.option_add("*TCombobox*Listbox.background", "#FFFFFF")
        self.root.option_add("*TCombobox*Listbox.foreground", "#26352B")
        self.root.option_add("*TCombobox*Listbox.selectBackground", "#D9F0E1")
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")
        self.root.option_add("*TCombobox*Listbox.borderWidth", 1)
        self.root.option_add("*TCombobox*Listbox.relief", "flat")

        shell = tk.Frame(self.root, bg="#F4F7F5")
        shell.pack(fill="both", expand=True)
        self.left = tk.Frame(shell, bg="#E8F6ED", width=215)
        self.left.pack(side="left", fill="y")
        self.left.pack_propagate(False)
        brand = tk.Frame(self.left, bg="#E8F6ED")
        brand.pack(fill="x", padx=18, pady=(24, 28))
        tk.Label(brand, text="✈", bg="#E8F6ED", fg="#31C7FF", font=("Segoe UI", 34, "bold")).pack(anchor="w")
        tk.Label(brand, text="FLIGHT PLANNER", bg="#E8F6ED", fg="#FFFFFF", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(4, 0))
        tk.Label(brand, text="Plan  ·  Explore  ·  Fly", bg="#E8F6ED", fg="#64756A", font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 0))
        self.nav_buttons = []
        nav_items = [
            ("⌂", "Dashboard", self.show_dashboard), ("✈", "Airports", self.show_airports),
            ("⌘", "Routes", self.show_routes), ("⌖", "Shortest Route", self.show_shortest_route),
            ("⇄", "Alternative Routes", self.show_alternatives), ("♧", "Visualize Network", self.show_visualization),
            ("▥", "Analytics", self.show_analytics), ("⚙", "Settings", self.show_settings),
            ("⇥", "Exit", self.root.destroy),
        ]
        for symbol, label, callback in nav_items:
            btn = tk.Button(self.left, text=f"  {symbol}    {label}", command=lambda cb=callback, name=label: self._navigate(cb, name),
                            anchor="w", relief="flat", bd=0, padx=12, pady=11,
                            bg="#E8F6ED", fg="#26352B", activebackground="#D9F0E1", activeforeground="#FFFFFF",
                            font=("Segoe UI", 10), cursor="hand2")
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons.append((label, btn))
        footer = tk.Frame(self.left, bg="#E8F6ED")
        footer.pack(side="bottom", fill="x", padx=20, pady=22)
        tk.Label(footer, text="✈  Smarter Routes\n    Better Connections", justify="left", bg="#E8F6ED", fg="#64B7F5", font=("Segoe UI", 9)).pack(anchor="w")

        main = tk.Frame(shell, bg="#F4F7F5")
        main.pack(side="left", fill="both", expand=True)
        header = tk.Frame(main, bg="#F4F7F5")
        header.pack(fill="x", padx=24, pady=(18, 8))
        self.page_heading = tk.Label(header, text="Welcome to Flight Route Planner", bg="#F4F7F5", fg="#26352B", font=("Segoe UI", 22, "bold"))
        self.page_heading.pack(anchor="w")
        tk.Label(header, text="Plan efficient routes across a simulated airport network.", bg="#F4F7F5", fg="#64756A", font=("Segoe UI", 10)).pack(anchor="w", pady=(5, 0))
        self.content = tk.Frame(main, bg="#F4F7F5")
        self.content.pack(side="top", fill="both", expand=True, padx=20, pady=(5, 8))
        self.status = tk.Label(main, text="Ready  •  Sample routes are simulated, not live aviation data", anchor="w", bg="#EAF3ED", fg="#64756A", padx=12, pady=7, font=("Segoe UI", 9))
        self.status.pack(side="bottom", fill="x")
        self.show_dashboard()

    def _navigate(self, callback, name):
        for label, btn in self.nav_buttons:
            btn.configure(bg="#D9F0E1" if label == name else "#E8F6ED", fg="#FFFFFF" if label == name else "#26352B")
        callback()

    def _set_status(self, text):
        self.status.config(text=text)

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def _table(self, parent, columns, rows, height=18):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, pady=8)
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=height)
        ybar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        xbar = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        for col in columns:
            tree.heading(col, text=col.replace("_", " ").title())
            tree.column(col, width=140, anchor="w")
        for row in rows:
            tree.insert("", "end", values=[row.get(c, "") for c in columns])
        tree.grid(row=0, column=0, sticky="nsew")
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1); frame.columnconfigure(0, weight=1)
        return tree

    def show_dashboard(self):
        """Build the full dashboard; route results stay on this page."""
        self.clear_content()
        self.page_heading.configure(text="✈  Welcome to Flight Route Planner")
        airports_df, routes_df = self.dm.load_airports(), self.dm.load_routes()
        stats = route_statistics(routes_df)
        self._dashboard_path = None
        bg, panel, border = "#F4F7F5", "#FFFFFF", "#BBDCC7"
        cyan, blue, green, muted = "#14A04B", "#168BFF", "#14A04B", "#64756A"

        # Summary cards: responsive and visually close to the target reference.
        cards = tk.Frame(self.content, bg=bg)
        cards.pack(fill="x", pady=(0, 10))
        metrics = [
            ("✈", "Airports", f"{len(airports_df)}", "Total airports in network", blue, "#E8F6ED"),
            ("⌁", "Routes", f"{len(routes_df)}", "Total routes available", green, "#E8F6ED"),
            ("⌖", "Shortest Leg", f"{stats.get('min', 0):,.0f} km" if stats.get("count") else "—", "Minimum distance between airports", "#7165B5", "#F0EEFC"),
            ("▥", "Average Leg", f"{stats.get('mean', 0):,.0f} km" if stats.get("count") else "—", "Average distance between airports", "#14A04B", "#E8F6ED"),
        ]
        for icon, title, value, desc, accent, tint in metrics:
            card = tk.Frame(cards, bg=panel, highlightbackground=border, highlightthickness=1, bd=0)
            card.pack(side="left", fill="both", expand=True, padx=(0, 8))
            top = tk.Frame(card, bg=panel); top.pack(fill="x", padx=12, pady=(10, 1))
            tk.Label(top, text=icon, bg=tint, fg=accent, font=("Segoe UI", 17, "bold"), width=3, pady=3).pack(side="left")
            tk.Label(top, text=title, bg=panel, fg=accent, font=("Segoe UI", 10, "bold")).pack(side="left", padx=9)
            tk.Label(card, text=value, bg=panel, fg=accent, font=("Segoe UI", 21, "bold")).pack(anchor="w", padx=14)
            tk.Label(card, text=desc, bg=panel, fg=muted, font=("Segoe UI", 8), wraplength=220, justify="left").pack(anchor="w", padx=13, pady=(0, 9))

        body = tk.Frame(self.content, bg=bg)
        body.pack(fill="both", expand=True)
        left_col = tk.Frame(body, bg=bg)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 9))
        right_col = tk.Frame(body, bg=bg)
        right_col.pack(side="left", fill="both", expand=True)

        def panel_frame(parent, title, icon="•"):
            frame = tk.LabelFrame(parent, text=f"  {icon}  {title}  ", bg=panel, fg="#26352B",
                                  font=("Segoe UI", 11, "bold"), bd=1, relief="solid",
                                  padx=10, pady=8, highlightbackground=border, highlightcolor=border)
            return frame

        # Route search: compute and render directly in dashboard.
        search = panel_frame(left_col, "Route Search", "⌕")
        search.pack(fill="x", pady=(0, 9))
        airports = airports_df.fillna("")
        codes = airports["code"].astype(str).str.strip().tolist() if "code" in airports else []
        names = {str(r.code).strip(): f"{str(r.code).strip()} — {str(getattr(r, 'city', '')).strip()}" for r in airports.itertuples()}
        fields = tk.Frame(search, bg=panel); fields.pack(fill="x")
        tk.Label(fields, text="From Airport", bg=panel, fg="#4D6254", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 7))
        tk.Label(fields, text="To Airport", bg=panel, fg="#4D6254", font=("Segoe UI", 9, "bold")).grid(row=0, column=1, sticky="w", padx=(7, 0))
        self.dash_source = ttk.Combobox(fields, values=[names.get(c, c) for c in codes], state="readonly", style="Airport.TCombobox", font=("Segoe UI", 11))
        self.dash_dest = ttk.Combobox(fields, values=[names.get(c, c) for c in codes], state="readonly", style="Airport.TCombobox", font=("Segoe UI", 11))
        self.dash_source.grid(row=1, column=0, sticky="ew", padx=(0, 7), pady=(5, 9), ipady=4)
        self.dash_dest.grid(row=1, column=1, sticky="ew", padx=(7, 0), pady=(5, 9), ipady=4)
        fields.columnconfigure(0, weight=1); fields.columnconfigure(1, weight=1)
        if codes:
            self.dash_source.current(0)
            self.dash_dest.current(min(3, len(codes)-1))
        ttk.Button(search, text="⌕  Find Shortest Route", style="Accent.TButton", command=self._dashboard_route).pack(fill="x")

        overview = panel_frame(left_col, "Route Overview", "⌖")
        overview.pack(fill="x", pady=(0, 9))
        self.dash_route_nodes = tk.Frame(overview, bg=panel)
        self.dash_route_nodes.pack(fill="x", pady=(2, 8))
        self.dash_route_stats = tk.Frame(overview, bg=panel)
        self.dash_route_stats.pack(fill="x")
        self.dash_route_map = tk.Canvas(self.dash_route_stats, height=70, bg="#F7FAF8", highlightthickness=1, highlightbackground=border)
        self.dash_route_map.pack(fill="x", pady=(7, 0))
        self._render_dashboard_route(None, None, None)

        popular = panel_frame(left_col, "Popular Connections", "▥")
        popular.pack(fill="both", expand=True)
        self.dash_popular_canvas = tk.Canvas(popular, height=145, bg=panel, highlightthickness=0)
        self.dash_popular_canvas.pack(fill="both", expand=True)
        self._draw_popular_connections(routes_df)
        self.dash_popular_canvas.bind("<Configure>", lambda e: self._draw_popular_connections(routes_df))

        network = panel_frame(right_col, "Network Snapshot", "♧")
        network.pack(fill="both", expand=True, pady=(0, 9))
        self.dash_network_canvas = tk.Canvas(network, height=250, bg="#EAF3ED", highlightthickness=1, highlightbackground="#DDE8E0")
        self.dash_network_canvas.pack(fill="both", expand=True)
        self.dash_network_canvas.bind("<Configure>", lambda e: self._draw_dashboard_network())
        tk.Label(network, text="● Start     ● Destination     ━ Shortest route     ━ Other routes", bg=panel, fg=muted, font=("Segoe UI", 8)).pack(anchor="w", pady=(5, 0))

        distribution = panel_frame(right_col, "Distance Distribution", "◔")
        distribution.pack(fill="both", expand=True)
        self.dash_hist_canvas = tk.Canvas(distribution, height=165, bg=panel, highlightthickness=0)
        self.dash_hist_canvas.pack(fill="both", expand=True)
        self._draw_distance_distribution(routes_df)
        self.dash_hist_canvas.bind("<Configure>", lambda e: self._draw_distance_distribution(routes_df))
        self._dashboard_routes_df = routes_df
        self._dashboard_graph = self._graph().G
        self._draw_dashboard_network()

    def _render_dashboard_route(self, path, distance, duration):
        """Refresh the route overview widgets without leaving the dashboard."""
        for widget in self.dash_route_nodes.winfo_children(): widget.destroy()
        self.dash_route_map.pack_forget()
        for widget in self.dash_route_stats.winfo_children():
            if widget is not self.dash_route_map: widget.destroy()
        if not path:
            tk.Label(self.dash_route_nodes, text="Choose two airports and find a route to see the path here.", bg="#FFFFFF", fg="#64756A", font=("Segoe UI", 9)).pack(anchor="w", pady=7)
            summary = "Total Distance\n—"
            time_text = "Estimated Duration\n—"
        else:
            for i, code in enumerate(path):
                node = tk.Frame(self.dash_route_nodes, bg="#FFFFFF")
                node.pack(side="left", expand=True, fill="x")
                tk.Label(node, text=f"●  {code}", bg="#FFFFFF", fg="#14A04B", font=("Segoe UI", 9, "bold")).pack(anchor="w")
                city = str(self._dashboard_graph.nodes[code].get("city", "")) if hasattr(self, "_dashboard_graph") and code in self._dashboard_graph else ""
                tk.Label(node, text=city, bg="#FFFFFF", fg="#64756A", font=("Segoe UI", 8)).pack(anchor="w", padx=(17, 0))
                if i < len(path)-1:
                    tk.Label(self.dash_route_nodes, text="→", bg="#FFFFFF", fg="#14A04B", font=("Segoe UI", 12)).pack(side="left", padx=2)
            summary = f"Total Distance\n{distance:,.1f} km"
            time_text = f"Estimated Duration\n{duration}" if duration else "Estimated Duration\nNot provided"
        tk.Label(self.dash_route_stats, text=f"⌖  {summary}", bg="#E8F6ED", fg="#26352B", font=("Segoe UI", 10, "bold"), justify="left", padx=12, pady=8).pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Label(self.dash_route_stats, text=f"◷  {time_text}", bg="#E8F6ED", fg="#26352B", font=("Segoe UI", 10, "bold"), justify="left", padx=12, pady=8).pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.dash_route_map.pack(fill="x", pady=(7, 0))
        self.dash_route_map.delete("all")
        w = max(self.dash_route_map.winfo_width(), 300); h = max(self.dash_route_map.winfo_height(), 65)
        if path:
            margin = 28; ymid = h/2; step = (w-2*margin)/max(1, len(path)-1)
            coords=[]
            for i, code in enumerate(path):
                x=margin+i*step; coords.append((x, ymid, code))
            for (x1,y1,_),(x2,y2,_) in zip(coords,coords[1:]): self.dash_route_map.create_line(x1,y1,x2,y2,fill="#14A04B",width=3)
            for i,(x,y,code) in enumerate(coords):
                color="#168BFF" if i==0 else "#FF9D42" if i==len(coords)-1 else "#14A04B"
                self.dash_route_map.create_oval(x-5,y-5,x+5,y+5,fill=color,outline="")
                self.dash_route_map.create_text(x,y+17,text=code,fill="#26352B",font=("Segoe UI",8,"bold"))

    def _draw_dashboard_network(self):
        if not hasattr(self, "dash_network_canvas") or not hasattr(self, "_dashboard_graph"): return
        canvas=self.dash_network_canvas; canvas.delete("all")
        graph=self._dashboard_graph; w=max(canvas.winfo_width(),300); h=max(canvas.winfo_height(),200)
        if graph.number_of_nodes()==0:
            canvas.create_text(w/2,h/2,text="No airport network data",fill="#64756A",font=("Segoe UI",10)); return
        pos=nx.spring_layout(graph,seed=42,weight="distance_km")
        xs=[v[0] for v in pos.values()]; ys=[v[1] for v in pos.values()]
        minx,maxx=min(xs),max(xs); miny,maxy=min(ys),max(ys)
        pad=30
        coords={n:(pad+(x-minx)/(maxx-minx or 1)*(w-2*pad),pad+(y-miny)/(maxy-miny or 1)*(h-2*pad)) for n,(x,y) in pos.items()}
        path=getattr(self,"_dashboard_path",None) or []
        selected={frozenset((a,b)) for a,b in zip(path,path[1:])}
        for a,b,data in graph.edges(data=True):
            x1,y1=coords[a]; x2,y2=coords[b]; hot=frozenset((a,b)) in selected
            canvas.create_line(x1,y1,x2,y2,fill="#14A04B" if hot else "#C7D2CB",width=3.2 if hot else 1.5)
            if w>500:
                canvas.create_text((x1+x2)/2,(y1+y2)/2-7,text=f"{data.get('distance_km',0):g}",fill="#64756A",font=("Segoe UI",7))
        for n,(x,y) in coords.items():
            if path and n==path[0]: fill="#168BFF"; outline="#168BFF"
            elif path and n==path[-1]: fill="#FF9D42"; outline="#FF9D42"
            elif n in path: fill="#F4F7F5"; outline="#14A04B"
            else: fill="#F4F7F5"; outline="#26352B"
            canvas.create_oval(x-6,y-6,x+6,y+6,fill=fill,outline=outline,width=2)
            label=str(n); anchor="w" if x<w*.55 else "e"; tx=x+9 if anchor=="w" else x-9
            canvas.create_text(tx,y-10,text=label,anchor=anchor,fill="#26352B",font=("Segoe UI",8,"bold"))

    def _draw_popular_connections(self, routes_df):
        c=self.dash_popular_canvas; c.delete("all"); w=max(c.winfo_width(),400); h=max(c.winfo_height(),130)
        if routes_df.empty: c.create_text(w/2,h/2,text="No route data",fill="#64756A"); return
        rows=routes_df.copy()
        rows["distance_km"]=__import__("pandas").to_numeric(rows["distance_km"],errors="coerce")
        rows=rows.dropna(subset=["distance_km"]).sort_values("distance_km",ascending=False).head(5)
        if rows.empty: return
        maxv=max(float(v) for v in rows["distance_km"]); labelw=min(150,w*.36); right=58; usable=max(20,w-labelw-right)
        for i,(_,r) in enumerate(rows.iterrows()):
            y=14+i*max(23,(h-18)/5); name=f"{r['source']} → {r['destination']}"
            c.create_text(labelw-8,y+6,text=name,anchor="e",fill="#4D6254",font=("Segoe UI",8))
            bw=usable*float(r["distance_km"])/maxv
            c.create_rectangle(labelw,y,labelw+bw,y+13,fill="#14A04B" if i%2==0 else "#168BFF",outline="")
            c.create_text(min(labelw+bw+5,w-3),y+6,text=f"{float(r['distance_km']):,.0f}",anchor="w",fill="#26352B",font=("Segoe UI",8))

    def _draw_distance_distribution(self, routes_df):
        c=self.dash_hist_canvas; c.delete("all"); w=max(c.winfo_width(),300); h=max(c.winfo_height(),150)
        if routes_df.empty or "distance_km" not in routes_df: c.create_text(w/2,h/2,text="No route data",fill="#64756A"); return
        import pandas as pd
        distances=pd.to_numeric(routes_df["distance_km"],errors="coerce").dropna()
        if distances.empty: return
        bins=[0,500,1000,1500,2000,3000,float("inf")]; labels=["0–500","501–1k","1–1.5k","1.5–2k","2–3k","3k+"]
        counts=[int(((distances>=bins[i]) & (distances<(bins[i+1] if i+1<len(bins) else float("inf")))).sum()) for i in range(len(labels))]
        maxcount=max(max(counts),1); left=28; bottom=h-28; top=12; plotw=w-left-7; ploth=bottom-top
        for tick in range(0,maxcount+1,max(1,(maxcount+3)//4)):
            y=bottom-ploth*tick/maxcount; c.create_line(left,y,w-5,y,fill="#DDE8E0"); c.create_text(left-8,y,text=str(tick),fill="#64756A",font=("Segoe UI",7))
        gap=plotw/len(counts); bw=gap*.62
        for i,val in enumerate(counts):
            x=left+i*gap+(gap-bw)/2; bh=ploth*val/maxcount
            c.create_rectangle(x,bottom-bh,x+bw,bottom,fill="#168BFF",outline="")
            c.create_text(x+bw/2,bottom-bh-7,text=str(val),fill="#26352B",font=("Segoe UI",8,"bold"))
            c.create_text(x+bw/2,bottom+10,text=labels[i],fill="#64756A",font=("Segoe UI",7))

    def _dashboard_route(self):
        """Calculate a route and update the dashboard in place (no page redirect)."""
        try:
            source = self.dash_source.get().split(" — ")[0].strip().upper()
            destination = self.dash_dest.get().split(" — ")[0].strip().upper()
            if not source or not destination:
                messagebox.showwarning("Select airports", "Choose both source and destination airports.")
                return
            if source == destination:
                messagebox.showwarning("Choose different airports", "Source and destination must be different.")
                return
            graph = self._graph().G
            path, distance = dijkstra(build_adj_from_nx(graph), source, destination)
            if not path:
                messagebox.showinfo("No route found", f"No connected route exists between {source} and {destination}.")
                return
            total_minutes = 0.0
            edge_times = [graph.get_edge_data(a, b, default={}).get("travel_time_min") for a, b in zip(path, path[1:])]
            has_time = bool(edge_times) and all(value is not None for value in edge_times)
            if has_time:
                total_minutes = sum(float(value) for value in edge_times)
            duration = (f"{int(total_minutes // 60)}h {int(total_minutes % 60)}m" if total_minutes >= 60 else f"{int(total_minutes)} min") if has_time else None
            self._dashboard_graph = graph
            self._dashboard_path = path
            self._render_dashboard_route(path, distance, duration)
            self._draw_dashboard_network()
            self._set_status(f"Shortest route: {' → '.join(path)}   •   {distance:,.1f} km")
        except Exception as exc:
            messagebox.showerror("Route search", str(exc))

    def show_settings(self):
        """Modern in-app settings page; actions never open another window/page."""
        self.clear_content()
        self.page_heading.configure(text="Preferences & About")
        bg, panel, muted, accent = "#F4F7F5", "#FFFFFF", "#64756A", "#14A04B"
        tk.Label(self.content, text="Your workspace", bg=bg, fg="#26352B", font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 4))
        tk.Label(self.content, text="Manage display preferences and check the data powering your route planner.", bg=bg, fg=muted, font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 16))
        grid = tk.Frame(self.content, bg=bg); grid.pack(fill="x")
        airports, routes = self.dm.load_airports(), self.dm.load_routes()
        for title, value, desc, color in [
            ("Airport records", str(len(airports)), "Loaded from data/airports.csv", accent),
            ("Route records", str(len(routes)), "Loaded from data/routes.csv", "#14A04B"),
            ("Route algorithm", "Dijkstra", "Minimum total distance", "#B79BFF")]:
            card=tk.Frame(grid,bg=panel,highlightbackground="#BBDCC7",highlightthickness=1,padx=18,pady=16)
            card.pack(side="left",fill="both",expand=True,padx=(0,10))
            tk.Label(card,text=title.upper(),bg=panel,fg=muted,font=("Segoe UI",9,"bold")).pack(anchor="w")
            tk.Label(card,text=value,bg=panel,fg=color,font=("Segoe UI",20,"bold")).pack(anchor="w",pady=5)
            tk.Label(card,text=desc,bg=panel,fg=muted,font=("Segoe UI",9)).pack(anchor="w")
        info=tk.LabelFrame(self.content,text="  Application information  ",bg=panel,fg="#26352B",font=("Segoe UI",11,"bold"),bd=1,relief="solid",padx=16,pady=14,highlightbackground="#BBDCC7")
        info.pack(fill="x",pady=18)
        for line in ["• Dark dashboard interface with embedded charts and network visualization", "• Airport and route updates are saved through the data manager", "• Sample route distances and durations are simulated, not live aviation data", "• All route results, charts and network maps are displayed inside this application"]:
            tk.Label(info,text=line,bg=panel,fg=muted,font=("Segoe UI",10),anchor="w").pack(fill="x",pady=5)
        row=tk.Frame(self.content,bg=bg);row.pack(anchor="w")
        tk.Button(row,text="↻  Refresh data view",command=lambda:self.show_settings(),bg="#EAF3ED",fg="#26352B",activebackground="#D9F0E1",relief="flat",padx=15,pady=9,font=("Segoe UI",10,"bold"),cursor="hand2").pack(side="left",padx=(0,8))
        tk.Button(row,text="⌂  Back to dashboard",command=self.show_dashboard,bg="#14A04B",fg="#E8F6ED",activebackground="#27F0B0",relief="flat",padx=15,pady=9,font=("Segoe UI",10,"bold"),cursor="hand2").pack(side="left")

    def show_airports(self):
        """Airport management with inline editing controls and a styled table."""
        self.clear_content(); self.page_heading.configure(text="Airport Management")
        bg,panel,muted,green="#F4F7F5","#FFFFFF","#64756A","#14A04B"
        tk.Label(self.content,text="Manage airport directory",bg=bg,fg="#26352B",font=("Segoe UI",15,"bold")).pack(anchor="w")
        tk.Label(self.content,text="Add, update or remove airports without leaving this workspace.",bg=bg,fg=muted,font=("Segoe UI",10)).pack(anchor="w",pady=(3,12))
        form=tk.LabelFrame(self.content,text="  Airport details  ",bg=panel,fg="#26352B",font=("Segoe UI",10,"bold"),bd=1,relief="solid",padx=12,pady=10,highlightbackground="#BBDCC7")
        form.pack(fill="x",pady=(0,10))
        fields={}
        for col,(label,key,width) in enumerate([("Airport code","code",12),("Airport name","name",30),("City","city",20)]):
            tk.Label(form,text=label,bg=panel,fg=muted,font=("Segoe UI",9,"bold")).grid(row=0,column=col,sticky="w",padx=(0,10))
            ent=tk.Entry(form,bg="#FFFFFF",fg="#26352B",insertbackground="#26352B",relief="flat",font=("Segoe UI",10),width=width,highlightthickness=1,highlightbackground="#BBDCC7",highlightcolor="#14A04B")
            ent.grid(row=1,column=col,sticky="ew",padx=(0,10),ipady=8);fields[key]=ent
            form.columnconfigure(col,weight=1)
        tree=self._table(self.content,["code","name","city"],self.dm.load_airports().to_dict("records"),height=11)
        def clear_form():
            for ent in fields.values(): ent.delete(0,"end")
        def refresh(select_code=None):
            for item in tree.get_children():tree.delete(item)
            for row in self.dm.load_airports().fillna("").to_dict("records"):
                iid=tree.insert("","end",values=[row.get(c,"") for c in ["code","name","city"]])
                if select_code and str(row.get("code","")).upper()==select_code.upper(): tree.selection_set(iid)
            self._set_status("Airport directory refreshed")
        def selected_row():
            sel=tree.selection()
            if not sel: messagebox.showinfo("Select airport","Select an airport row first.");return None
            vals=tree.item(sel[0],"values")
            return vals
        def load_selected(_event=None):
            vals=selected_row()
            if vals:
                for key,val in zip(["code","name","city"],vals):
                    fields[key].delete(0,"end");fields[key].insert(0,val)
        tree.bind("<<TreeviewSelect>>",load_selected)
        def add():
            try:
                obj=Airport(fields["code"].get(),fields["name"].get(),fields["city"].get())
                if not obj.code or not obj.name or not obj.city: raise ValueError("Complete all three airport fields.")
                self.dm.add_airport(obj);refresh(obj.code);self._set_status(f"Added airport {obj.code}")
            except Exception as exc:messagebox.showerror("Could not add airport",str(exc))
        def update():
            vals=selected_row()
            if not vals:return
            try:
                code=vals[0]
                self.dm.update_airport(code,name=fields["name"].get(),city=fields["city"].get())
                refresh(code);self._set_status(f"Updated airport {code}")
            except Exception as exc:messagebox.showerror("Could not update airport",str(exc))
        def delete():
            vals=selected_row()
            if not vals:return
            if messagebox.askyesno("Delete airport",f"Delete {vals[0]} and its connected routes?"):
                try:self.dm.delete_airport(vals[0]);refresh();clear_form();self._set_status(f"Deleted airport {vals[0]}")
                except Exception as exc:messagebox.showerror("Could not delete airport",str(exc))
        controls=tk.Frame(form,bg=panel);controls.grid(row=2,column=0,columnspan=3,sticky="w",pady=(10,0))
        for label,cmd,color in [("＋ Add airport",add,green),("✎ Update selected",update,"#168BFF"),("− Delete selected",delete,"#D96879"),("Clear",clear_form,"#EAF3ED")]:
            tk.Button(controls,text=label,command=cmd,bg=color,fg="#E8F6ED" if color==green else "#26352B",activebackground=color,relief="flat",padx=12,pady=7,font=("Segoe UI",9,"bold"),cursor="hand2").pack(side="left",padx=(0,7))

    def show_routes(self):
        """Route management page with inline form and no external redirects."""
        self.clear_content(); self.page_heading.configure(text="Route Management")
        bg,panel,muted="#F4F7F5","#FFFFFF","#64756A"
        tk.Label(self.content,text="Manage network connections",bg=bg,fg="#26352B",font=("Segoe UI",15,"bold")).pack(anchor="w")
        tk.Label(self.content,text="Each connection is a weighted graph edge. Distances must be positive.",bg=bg,fg=muted,font=("Segoe UI",10)).pack(anchor="w",pady=(3,12))
        form=tk.LabelFrame(self.content,text="  Connection details  ",bg=panel,fg="#26352B",font=("Segoe UI",10,"bold"),bd=1,relief="solid",padx=12,pady=10,highlightbackground="#BBDCC7")
        form.pack(fill="x",pady=(0,10))
        codes=self.dm.load_airports().fillna("")["code"].astype(str).tolist()
        entries={}
        labels=[("Source","source",codes),("Destination","destination",codes),("Distance (km)","distance_km",None),("Duration (minutes)","travel_time_min",None)]
        for col,(label,key,values) in enumerate(labels):
            tk.Label(form,text=label,bg=panel,fg=muted,font=("Segoe UI",9,"bold")).grid(row=0,column=col,sticky="w",padx=(0,9))
            if values is not None:
                widget=ttk.Combobox(form,values=values,state="readonly",width=15,font=("Segoe UI",10),style="Airport.TCombobox")
                widget.configure(style="Airport.TCombobox")
            else:
                widget=tk.Entry(form,bg="#FFFFFF",fg="#26352B",insertbackground="#26352B",relief="flat",font=("Segoe UI",10),width=16,highlightthickness=1,highlightbackground="#BBDCC7")
            widget.grid(row=1,column=col,sticky="ew",padx=(0,9),ipady=7);entries[key]=widget;form.columnconfigure(col,weight=1)
        cols=["source","destination","distance_km","travel_time_min"]
        tree=self._table(self.content,cols,self.dm.load_routes().fillna("").to_dict("records"),height=11)
        def get(key):
            widget=entries[key]
            return widget.get().strip()
        def setval(key,value):
            widget=entries[key]
            if isinstance(widget,ttk.Combobox):widget.set(value)
            else:widget.delete(0,"end");widget.insert(0,value)
        def clear_form():
            for widget in entries.values():
                if isinstance(widget,ttk.Combobox):widget.set("")
                else:widget.delete(0,"end")
        def refresh():
            for item in tree.get_children():tree.delete(item)
            for row in self.dm.load_routes().fillna("").to_dict("records"):tree.insert("","end",values=[row.get(c,"") for c in cols])
            self._set_status("Route connections refreshed")
        def selected(_event=None):
            sel=tree.selection()
            if not sel:return None
            vals=tree.item(sel[0],"values")
            for key,val in zip(cols,vals):setval(key,val)
            return vals
        tree.bind("<<TreeviewSelect>>",selected)
        def add():
            try:
                if not get("source") or not get("destination") or not get("distance_km"):raise ValueError("Choose source, destination and distance.")
                distance=float(get("distance_km"));duration=get("travel_time_min")
                self.dm.add_route(FlightRoute(get("source"),get("destination"),distance,duration or None));refresh();self._set_status("Route connection added")
            except Exception as exc:messagebox.showerror("Could not add route",str(exc))
        def update():
            sel=tree.selection()
            if not sel:return messagebox.showinfo("Select route","Select a route row first.")
            try:
                idx=tree.index(sel[0]);distance=float(get("distance_km"));duration=get("travel_time_min")
                # Replacing the selected row through the data manager keeps CSV persistence centralized.
                self.dm.delete_route(idx);self.dm.add_route(FlightRoute(get("source"),get("destination"),distance,duration or None));refresh();self._set_status("Route connection updated")
            except Exception as exc:messagebox.showerror("Could not update route",str(exc))
        def delete():
            sel=tree.selection()
            if not sel:return messagebox.showinfo("Select route","Select a route row first.")
            idx=tree.index(sel[0])
            if messagebox.askyesno("Delete route","Remove the selected connection?"):
                try:self.dm.delete_route(idx);refresh();clear_form();self._set_status("Route connection deleted")
                except Exception as exc:messagebox.showerror("Could not delete route",str(exc))
        controls=tk.Frame(form,bg=panel);controls.grid(row=2,column=0,columnspan=4,sticky="w",pady=(10,0))
        for label,cmd,color in [("＋ Add route",add,"#14A04B"),("✎ Update selected",update,"#168BFF"),("− Delete selected",delete,"#D96879"),("Clear",clear_form,"#EAF3ED")]:
            tk.Button(controls,text=label,command=cmd,bg=color,fg="#E8F6ED" if color=="#14A04B" else "#26352B",activebackground=color,relief="flat",padx=12,pady=7,font=("Segoe UI",9,"bold"),cursor="hand2").pack(side="left",padx=(0,7))

    def show_airports(self):
        self.clear_content()
        self.page_heading.configure(text="Airport Management")
        ttk.Label(self.content, text="Airport Management", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tree = self._table(self.content, ["code", "name", "city"], self.dm.load_airports().to_dict("records"))
        controls = ttk.Frame(self.content); controls.pack(fill="x", pady=6)
        def refresh():
            for item in tree.get_children(): tree.delete(item)
            for row in self.dm.load_airports().to_dict("records"):
                tree.insert("", "end", values=[row[c] for c in ["code", "name", "city"]])
            self._set_status("Airport list refreshed")
        def add():
            code = simpledialog.askstring("Add airport", "Airport code:", parent=self.root)
            if code is None: return
            name = simpledialog.askstring("Add airport", "Airport name:", parent=self.root)
            if name is None: return
            city = simpledialog.askstring("Add airport", "City:", parent=self.root)
            if city is None: return
            try:
                self.dm.add_airport(Airport(code, name, city)); refresh()
            except Exception as exc: messagebox.showerror("Could not add airport", str(exc))
        def edit():
            selected = tree.selection()
            if not selected: return messagebox.showwarning("Select airport", "Select an airport first.")
            code, name0, city0 = tree.item(selected[0], "values")
            name = simpledialog.askstring("Update airport", "Airport name:", initialvalue=name0, parent=self.root)
            if name is None: return
            city = simpledialog.askstring("Update airport", "City:", initialvalue=city0, parent=self.root)
            if city is None: return
            try: self.dm.update_airport(code, name=name, city=city); refresh()
            except Exception as exc: messagebox.showerror("Could not update airport", str(exc))
        def delete():
            selected = tree.selection()
            if not selected: return messagebox.showwarning("Select airport", "Select an airport first.")
            code = tree.item(selected[0], "values")[0]
            if messagebox.askyesno("Confirm deletion", f"Delete {code} and its connected routes?"):
                try: self.dm.delete_airport(code); refresh()
                except Exception as exc: messagebox.showerror("Could not delete airport", str(exc))
        for label, command in [("Add Airport", add), ("Update Selected", edit), ("Delete Selected", delete), ("Refresh", refresh)]:
            ttk.Button(controls, text=label, command=command).pack(side="left", padx=4)

    def show_routes(self):
        self.clear_content()
        self.page_heading.configure(text="Route Management")
        ttk.Label(self.content, text="Route Management", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        columns = ["source", "destination", "distance_km", "travel_time_min"]
        tree = self._table(self.content, columns, self.dm.load_routes().to_dict("records"))
        controls = ttk.Frame(self.content); controls.pack(fill="x", pady=6)
        def refresh():
            for item in tree.get_children(): tree.delete(item)
            for row in self.dm.load_routes().to_dict("records"):
                tree.insert("", "end", values=[row.get(c, "") for c in columns])
            self._set_status("Route list refreshed")
        def add():
            airports = self.dm.load_airports()["code"].tolist()
            if len(airports) < 2: return messagebox.showwarning("Need airports", "Add at least two airports first.")
            source = simpledialog.askstring("Add route", f"Source code ({', '.join(airports)}):", parent=self.root)
            if source is None: return
            destination = simpledialog.askstring("Add route", "Destination code:", parent=self.root)
            if destination is None: return
            distance = simpledialog.askfloat("Add route", "Distance in km (positive):", minvalue=0.000001, parent=self.root)
            if distance is None: return
            travel_time = simpledialog.askstring("Add route", "Estimated travel time in minutes (optional):", parent=self.root)
            if travel_time is None: return
            try:
                self.dm.add_route(FlightRoute(source, destination, distance, travel_time.strip() or None)); refresh()
            except Exception as exc: messagebox.showerror("Could not add route", str(exc))
        def edit():
            selected = tree.selection()
            if not selected: return messagebox.showwarning("Select route", "Select a route first.")
            idx = tree.index(selected[0])
            row = tree.item(selected[0], "values")
            distance = simpledialog.askfloat("Update route", "New distance in km:", initialvalue=float(row[2]), minvalue=0.000001, parent=self.root)
            if distance is None: return
            current_time = row[3]
            travel_time = simpledialog.askstring("Update route", "New travel time in minutes (blank to clear):", initialvalue="" if current_time == "nan" else str(current_time), parent=self.root)
            if travel_time is None: return
            try: self.dm.update_route(idx, distance_km=distance, travel_time_min=travel_time.strip()); refresh()
            except Exception as exc: messagebox.showerror("Could not update route", str(exc))
        def delete():
            selected = tree.selection()
            if not selected: return messagebox.showwarning("Select route", "Select a route first.")
            idx = tree.index(selected[0])
            if messagebox.askyesno("Confirm deletion", "Delete the selected route?"):
                try: self.dm.delete_route(idx); refresh()
                except Exception as exc: messagebox.showerror("Could not delete route", str(exc))
        for label, command in [("Add Route", add), ("Update Selected", edit), ("Delete Selected", delete), ("Refresh", refresh)]:
            ttk.Button(controls, text=label, command=command).pack(side="left", padx=4)

    def _graph(self):
        return GraphManager(self.dm.load_airports(), self.dm.load_routes())

    def _airport_picker(self, parent):
        codes = self.dm.load_airports()["code"].tolist()
        ttk.Label(parent, text="Source airport:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        source = ttk.Combobox(parent, values=codes, state="readonly", width=18, style="Airport.TCombobox", font=("Segoe UI", 11))
        source.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(parent, text="Destination airport:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        destination = ttk.Combobox(parent, values=codes, state="readonly", width=18, style="Airport.TCombobox", font=("Segoe UI", 11))
        destination.grid(row=1, column=1, padx=5, pady=5)
        self.route_source_picker = source
        self.route_destination_picker = destination
        return source, destination

    def show_shortest_route(self):
        """Modern route finder with airport selectors and an embedded live network map."""
        self.clear_content()
        self.page_heading.configure(text="Shortest Route Finder")
        bg, panel, border = "#F4F7F5", "#FFFFFF", "#BBDCC7"
        text, muted, cyan, blue, green, orange = "#26352B", "#64756A", "#14A04B", "#168BFF", "#14A04B", "#FFAD62"

        intro = tk.Label(self.content, text="Find the most efficient connection between two airports.",
                         bg=bg, fg=muted, font=("Segoe UI", 10))
        intro.pack(anchor="w", pady=(0, 12))

        airports_df = self.dm.load_airports().fillna("")
        if len(airports_df) < 2:
            tk.Label(self.content, text="Add at least two airports before searching.", bg=bg, fg=text,
                     font=("Segoe UI", 11)).pack(anchor="w")
            return
        codes = airports_df["code"].astype(str).str.strip().tolist()
        labels = {}
        for row in airports_df.to_dict("records"):
            code = str(row.get("code", "")).strip().upper()
            city = str(row.get("city", "")).strip()
            name = str(row.get("name", "")).strip()
            labels[code] = f"{code}  ·  {city or name or 'Airport'}"
        choices = [labels[c] for c in codes]

        def card(parent, title, subtitle=None):
            box = tk.LabelFrame(parent, text=f"  {title}  ", bg=panel, fg=text,
                                font=("Segoe UI", 11, "bold"), bd=1, relief="solid",
                                padx=14, pady=12, highlightbackground=border, highlightcolor=border)
            if subtitle:
                tk.Label(box, text=subtitle, bg=panel, fg=muted,
                         font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 9))
            return box

        picker = card(self.content, "Route Planner", "Choose a starting airport and destination to calculate the shortest-distance route.")
        picker.pack(fill="x", pady=(0, 12))
        fields = tk.Frame(picker, bg=panel)
        fields.pack(fill="x")
        fields.columnconfigure(0, weight=1)
        fields.columnconfigure(1, weight=0)
        fields.columnconfigure(2, weight=1)
        tk.Label(fields, text="FROM AIRPORT", bg=panel, fg=muted,
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
        tk.Label(fields, text="TO AIRPORT", bg=panel, fg=muted,
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="w", pady=(0, 5))

        source = ttk.Combobox(fields, values=choices, state="readonly", style="Airport.TCombobox", font=("Segoe UI", 11))
        destination = ttk.Combobox(fields, values=choices, state="readonly", style="Airport.TCombobox", font=("Segoe UI", 11))
        source.grid(row=1, column=0, sticky="ew", padx=(0, 12), ipady=3)
        destination.grid(row=1, column=2, sticky="ew", padx=(12, 0), ipady=3)
        source.current(codes.index("JFK") if "JFK" in codes else 0)
        destination.current(codes.index("LAX") if "LAX" in codes and len(codes) > 1 else min(1, len(codes)-1))

        def swap_airports():
            a, b = source.current(), destination.current()
            source.current(b if b >= 0 else 0)
            destination.current(a if a >= 0 else min(1, len(codes)-1))

        tk.Button(fields, text="⇄", command=swap_airports, bg="#EAF3ED", fg=cyan,
                  activebackground="#D9F0E1", activeforeground=text, relief="flat", bd=0,
                  font=("Segoe UI", 17, "bold"), cursor="hand2", width=3).grid(row=1, column=1, padx=2)
        action_row = tk.Frame(picker, bg=panel)
        action_row.pack(fill="x", pady=(12, 0))
        tk.Button(action_row, text="✦  Find Shortest Route", command=lambda: calculate(),
                  bg=green, fg="#E8F6ED", activebackground="#27F0B0", activeforeground="#E8F6ED",
                  relief="flat", bd=0, padx=18, pady=10, font=("Segoe UI", 10, "bold"), cursor="hand2").pack(side="left")
        status_msg = tk.Label(action_row, text="Uses Dijkstra's algorithm · distance in kilometres",
                              bg=panel, fg=muted, font=("Segoe UI", 9))
        status_msg.pack(side="left", padx=14)

        result_area = tk.Frame(self.content, bg=bg)
        result_area.pack(fill="both", expand=True)
        summary = tk.Frame(result_area, bg=bg)
        summary.pack(fill="x", pady=(0, 10))
        metric_specs = [("TOTAL DISTANCE", "—", cyan), ("FLIGHT LEGS", "—", green), ("EST. DURATION", "—", orange)]
        metric_values = []
        for title, value, accent in metric_specs:
            m = tk.Frame(summary, bg=panel, highlightbackground=border, highlightthickness=1, padx=14, pady=9)
            m.pack(side="left", fill="x", expand=True, padx=(0, 8))
            tk.Label(m, text=title, bg=panel, fg=muted, font=("Segoe UI", 8, "bold")).pack(anchor="w")
            v = tk.Label(m, text=value, bg=panel, fg=accent, font=("Segoe UI", 18, "bold"))
            v.pack(anchor="w", pady=(3, 0))
            metric_values.append(v)

        lower = tk.Frame(result_area, bg=bg)
        lower.pack(fill="both", expand=True)
        path_card = card(lower, "Route Breakdown")
        path_card.pack(side="left", fill="y", padx=(0, 10))
        path_card.configure(width=250)
        path_card.pack_propagate(False)
        route_path = tk.Frame(path_card, bg=panel)
        route_path.pack(fill="both", expand=True, anchor="nw")
        tk.Label(route_path, text="Your selected route will appear here,\nwith each airport in order.",
                 bg=panel, fg=muted, justify="left", font=("Segoe UI", 9)).pack(anchor="w", pady=5)

        map_card = card(lower, "Airport Network", "The highlighted green line shows the calculated shortest path.")
        map_card.pack(side="left", fill="both", expand=True)
        network_canvas = tk.Canvas(map_card, bg="#EAF3ED", highlightthickness=1,
                                   highlightbackground="#DDE8E0", bd=0, height=300)
        network_canvas.pack(fill="both", expand=True)
        legend = tk.Frame(map_card, bg=panel)
        legend.pack(fill="x", pady=(8, 0))
        tk.Label(legend, text="●  Start", bg=panel, fg=blue, font=("Segoe UI", 8, "bold")).pack(side="left", padx=(0, 12))
        tk.Label(legend, text="●  Destination", bg=panel, fg=orange, font=("Segoe UI", 8, "bold")).pack(side="left", padx=(0, 12))
        tk.Label(legend, text="━  Shortest route", bg=panel, fg=green, font=("Segoe UI", 8, "bold")).pack(side="left")

        state = {"graph": self._graph().G, "path": []}

        def draw_network():
            canvas = network_canvas
            canvas.delete("all")
            graph = state["graph"]
            w, h = max(canvas.winfo_width(), 420), max(canvas.winfo_height(), 260)
            if graph.number_of_nodes() == 0:
                canvas.create_text(w/2, h/2, text="No airport data available", fill=muted, font=("Segoe UI", 11))
                return
            pos = nx.spring_layout(graph, seed=42, weight="distance_km")
            xs = [xy[0] for xy in pos.values()]; ys = [xy[1] for xy in pos.values()]
            minx, maxx = min(xs), max(xs); miny, maxy = min(ys), max(ys)
            pad = 38
            coords = {n: (pad + (xy[0]-minx)/(maxx-minx or 1)*(w-2*pad),
                          pad + (xy[1]-miny)/(maxy-miny or 1)*(h-2*pad)) for n, xy in pos.items()}
            path = state["path"]
            active_edges = {frozenset((a, b)) for a, b in zip(path, path[1:])}
            for a, b, data in graph.edges(data=True):
                x1, y1 = coords[a]; x2, y2 = coords[b]
                active = frozenset((a, b)) in active_edges
                canvas.create_line(x1, y1, x2, y2, fill=green if active else "#C7D2CB",
                                   width=4 if active else 1.5, smooth=True)
                if w > 600:
                    canvas.create_text((x1+x2)/2, (y1+y2)/2-7,
                                       text=f"{data.get('distance_km', 0):,.0f}", fill="#64756A",
                                       font=("Segoe UI", 7))
            for node, (x, y) in coords.items():
                if path and node == path[0]: fill, outline = blue, blue
                elif path and node == path[-1]: fill, outline = orange, orange
                elif node in path: fill, outline = "#E8F6ED", green
                else: fill, outline = "#F4F7F5", "#A9C8E5"
                radius = 7 if node in path else 5
                canvas.create_oval(x-radius, y-radius, x+radius, y+radius, fill=fill, outline=outline, width=2)
                anchor = "w" if x < w*0.55 else "e"
                canvas.create_text(x+(10 if anchor == "w" else -10), y-11, text=str(node), anchor=anchor,
                                   fill=text, font=("Segoe UI", 8, "bold"))

        def calculate():
            s = source.get().split("  ·  ")[0].strip().upper()
            t = destination.get().split("  ·  ")[0].strip().upper()
            if not s or not t:
                status_msg.configure(text="Choose both airports to continue.", fg=orange)
                return
            if s == t:
                status_msg.configure(text="Choose two different airports.", fg=orange)
                return
            try:
                graph = self._graph().G
                path, distance = dijkstra(build_adj_from_nx(graph), s, t)
                total_minutes = 0.0
                times = [graph.get_edge_data(a, b, default={}).get("travel_time_min") for a, b in zip(path, path[1:])]
                has_time = bool(times) and all(value is not None for value in times)
                if has_time:
                    total_minutes = sum(float(value) for value in times)
                    duration = f"{int(total_minutes // 60)}h {int(total_minutes % 60)}m" if total_minutes >= 60 else f"{int(total_minutes)} min"
                else:
                    duration = "Not provided"
                metric_values[0].configure(text=f"{distance:,.1f} km")
                metric_values[1].configure(text=str(len(path)-1))
                metric_values[2].configure(text=duration)
                for child in route_path.winfo_children():
                    child.destroy()
                tk.Label(route_path, text=f"{s}  →  {t}", bg=panel, fg=green,
                         font=("Segoe UI", 12, "bold"), wraplength=210).pack(anchor="w", pady=(0, 10))
                for i, code in enumerate(path):
                    node_frame = tk.Frame(route_path, bg="#E8F6ED", padx=9, pady=8)
                    node_frame.pack(fill="x", pady=3)
                    tk.Label(node_frame, text=("START" if i == 0 else "DESTINATION" if i == len(path)-1 else f"STOP {i}"),
                             bg="#E8F6ED", fg=(blue if i == 0 else orange if i == len(path)-1 else green),
                             font=("Segoe UI", 7, "bold")).pack(anchor="w")
                    city = str(graph.nodes[code].get("city", ""))
                    tk.Label(node_frame, text=code, bg="#E8F6ED", fg=text,
                             font=("Segoe UI", 12, "bold")).pack(anchor="w")
                    tk.Label(node_frame, text=city, bg="#E8F6ED", fg=muted,
                             font=("Segoe UI", 8), wraplength=205).pack(anchor="w")
                    if i < len(path)-1:
                        tk.Label(route_path, text="↓", bg=panel, fg=green,
                                 font=("Segoe UI", 12, "bold")).pack(anchor="center")
                state["graph"], state["path"] = graph, path
                draw_network()
                status_msg.configure(text=f"Route found · {len(path)-1} connection(s)", fg=green)
                self._set_status(f"Shortest route: {' → '.join(path)}  •  {distance:,.1f} km")
            except Exception as exc:
                status_msg.configure(text=f"Could not find route: {exc}", fg=orange)
                self._set_status("Route search could not be completed")

        network_canvas.bind("<Configure>", lambda event: draw_network())
        # Draw the real network immediately; calculate route results only when requested.
        draw_network()

    def show_alternatives(self):
        """Interactive route comparison with airport pickers and an in-page map."""
        self.clear_content()
        self.page_heading.configure(text="Alternative Routes")
        bg, panel, border = "#F4F7F5", "#FFFFFF", "#BBDCC7"
        text, muted, green, blue = "#26352B", "#64756A", "#14A04B", "#168BFF"

        tk.Label(self.content, text="Compare possible journeys", bg=bg, fg=text,
                 font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tk.Label(self.content, text="Compare distance, connections and the path on the airport network.",
                 bg=bg, fg=muted, font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 14))

        airports = self.dm.load_airports().fillna("")
        codes = [str(c).strip().upper() for c in airports.get("code", []) if str(c).strip()]
        if len(codes) < 2:
            tk.Label(self.content, text="Add at least two airports before comparing routes.",
                     bg=bg, fg=muted, font=("Segoe UI", 11)).pack(anchor="w")
            return
        names = {}
        for row in airports.to_dict("records"):
            code = str(row.get("code", "")).strip().upper()
            names[code] = f"{code}   ·   {row.get('city') or row.get('name') or 'Airport'}"
        choices = [names[c] for c in codes]

        selector = tk.Frame(self.content, bg=panel, highlightbackground=border,
                            highlightthickness=1, padx=16, pady=14)
        selector.pack(fill="x", pady=(0, 14))
        tk.Label(selector, text="FROM AIRPORT", bg=panel, fg=muted,
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(selector, text="TO AIRPORT", bg=panel, fg=muted,
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=2, sticky="w")
        src = ttk.Combobox(selector, values=choices, state="readonly", style="Airport.TCombobox", font=("Segoe UI", 11))
        dst = ttk.Combobox(selector, values=choices, state="readonly", style="Airport.TCombobox", font=("Segoe UI", 11))
        src.grid(row=1, column=0, sticky="ew", pady=(6, 0), ipady=5)
        dst.grid(row=1, column=2, sticky="ew", pady=(6, 0), ipady=5)
        src.current(0)
        dst.current(min(1, len(codes) - 1))
        selector.columnconfigure(0, weight=1)
        selector.columnconfigure(2, weight=1)

        def swap_locations():
            a, b = src.current(), dst.current()
            src.current(b if b >= 0 else 0)
            dst.current(a if a >= 0 else min(1, len(codes) - 1))

        tk.Button(selector, text="⇄", command=swap_locations, bg="#EAF3ED", fg=text,
                  activebackground="#D9F0E1", activeforeground=text, relief="flat",
                  font=("Segoe UI", 16, "bold"), cursor="hand2", width=4).grid(row=1, column=1, padx=10, pady=(6, 0))

        actions = tk.Frame(selector, bg=panel)
        actions.grid(row=2, column=0, columnspan=3, sticky="w", pady=(12, 0))
        results_area = tk.Frame(self.content, bg=bg)
        results_area.pack(fill="both", expand=True)
        left = tk.Frame(results_area, bg=bg)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))
        right = tk.Frame(results_area, bg=panel, highlightbackground=border, highlightthickness=1, padx=12, pady=12)
        right.pack(side="left", fill="both", expand=True)
        tk.Label(left, text="AVAILABLE ROUTES", bg=bg, fg=text,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
        cards_area = tk.Frame(left, bg=bg)
        cards_area.pack(fill="both", expand=True)
        tk.Label(right, text="ROUTE NETWORK", bg=panel, fg=text,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(right, text="Select a route card to highlight its path.", bg=panel, fg=muted,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 8))
        map_canvas = tk.Canvas(right, bg="#EAF3ED", highlightthickness=1,
                               highlightbackground=border, bd=0, height=300)
        map_canvas.pack(fill="both", expand=True)
        legend = tk.Frame(right, bg=panel)
        legend.pack(fill="x", pady=(8, 0))
        for label, color in [("● Start", blue), ("● Destination", "#FFAD62"), ("━ Selected path", green)]:
            tk.Label(legend, text=label, bg=panel, fg=color, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 12))

        state = {"graph": None, "routes": [], "selected": 0}

        def code_from(combo):
            value = combo.get()
            return value.split("   ·   ")[0].strip().upper()

        def draw_map(_event=None):
            map_canvas.delete("all")
            graph = state["graph"]
            if graph is None or graph.number_of_nodes() == 0:
                return
            w, h = max(map_canvas.winfo_width(), 350), max(map_canvas.winfo_height(), 260)
            pos = nx.spring_layout(graph, seed=42, weight="distance_km", iterations=60)
            xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
            pad = 35
            coords = {n: (pad + (p[0] - min(xs)) / (max(xs) - min(xs) or 1) * (w - 2 * pad),
                          pad + (p[1] - min(ys)) / (max(ys) - min(ys) or 1) * (h - 2 * pad)) for n, p in pos.items()}
            chosen = state["routes"][state["selected"]][0] if state["routes"] else []
            path_edges = {frozenset((a, b)) for a, b in zip(chosen, chosen[1:])}
            for a, b, data in graph.edges(data=True):
                x1, y1 = coords[a]; x2, y2 = coords[b]
                is_path = frozenset((a, b)) in path_edges
                map_canvas.create_line(x1, y1, x2, y2, fill=green if is_path else "#C7D2CB",
                                       width=4 if is_path else 1.5)
                if w > 500:
                    map_canvas.create_text((x1+x2)/2, (y1+y2)/2-7,
                                           text=f"{data.get('distance_km', 0):,.0f}",
                                           fill="#6D98B7", font=("Segoe UI", 7))
            for node, (x, y) in coords.items():
                if chosen and node == chosen[0]:
                    fill, outline = blue, blue
                elif chosen and node == chosen[-1]:
                    fill, outline = "#FFAD62", "#FFAD62"
                elif node in chosen:
                    fill, outline = green, green
                else:
                    fill, outline = "#EAF3ED", "#14A04B"
                map_canvas.create_oval(x-6, y-6, x+6, y+6, fill=fill, outline=outline, width=2)
                anchor = "w" if x < w * .58 else "e"
                map_canvas.create_text(x+(9 if anchor == "w" else -9), y-11, text=str(node),
                                       anchor=anchor, fill=text, font=("Segoe UI", 8, "bold"))

        def select_route(index):
            state["selected"] = index
            for i, widgets in enumerate(state.get("card_widgets", [])):
                frame, bar, label = widgets
                active = i == index
                frame.configure(highlightbackground=green if active else border, bg="#E8F6ED" if active else panel)
                bar.configure(bg=green if i == 0 else blue)
                label.configure(fg=green if active else muted)
            draw_map()

        def compare():
            for widget in cards_area.winfo_children():
                widget.destroy()
            state["routes"] = []
            state["card_widgets"] = []
            source, target = code_from(src), code_from(dst)
            if source == target:
                tk.Label(cards_area, text="Choose two different airports.", bg=bg, fg="#FFAD62",
                         font=("Segoe UI", 10)).pack(anchor="w")
                state["graph"] = None; draw_map(); return
            graph = self._graph().G
            try:
                candidates = find_alternative_paths(graph, source, target, k=3)
            except Exception as exc:
                tk.Label(cards_area, text=f"No connected route found: {exc}", bg=bg, fg="#FFAD62",
                         font=("Segoe UI", 10), wraplength=480, justify="left").pack(anchor="w")
                state["graph"] = graph; draw_map(); return
            if not candidates:
                tk.Label(cards_area, text="No connected route exists for this airport pair.", bg=bg,
                         fg=muted, font=("Segoe UI", 10)).pack(anchor="w")
                state["graph"] = graph; draw_map(); return
            state["graph"], state["routes"], state["selected"] = graph, candidates, 0
            max_distance = max(distance for _, distance in candidates) or 1
            for i, (path, distance) in enumerate(candidates):
                frame = tk.Frame(cards_area, bg="#E8F6ED" if i == 0 else panel,
                                 highlightbackground=green if i == 0 else border, highlightthickness=1,
                                 padx=13, pady=11, cursor="hand2")
                frame.pack(fill="x", pady=(0, 9))
                head = tk.Frame(frame, bg=frame.cget("bg")); head.pack(fill="x")
                tk.Label(head, text=("★  SHORTEST OPTION" if i == 0 else f"ROUTE OPTION 0{i+1}"),
                         bg=head.cget("bg"), fg=green if i == 0 else blue,
                         font=("Segoe UI", 9, "bold")).pack(side="left")
                tk.Label(head, text=f"{distance:,.1f} km", bg=head.cget("bg"), fg=text,
                         font=("Segoe UI", 15, "bold")).pack(side="right")
                route_label = tk.Label(frame, text="  →  ".join(path), bg=frame.cget("bg"), fg=text,
                                       font=("Segoe UI", 11, "bold"), anchor="w", wraplength=650, justify="left")
                route_label.pack(anchor="w", pady=(9, 7))
                bar_bg = tk.Frame(frame, bg="#102B40", height=7); bar_bg.pack(fill="x"); bar_bg.pack_propagate(False)
                bar = tk.Frame(bar_bg, bg=green if i == 0 else blue, height=7); bar.pack(side="left", fill="y")
                bar.bind("<Configure>", lambda e: None)
                # Relative distance bar is redrawn to the card's actual width.
                def resize_bar(event, bar=bar, distance=distance):
                    bar.configure(width=max(4, int(event.width * distance / max_distance)))
                bar_bg.bind("<Configure>", resize_bar)
                tk.Label(frame, text=f"{len(path)-1} connection(s)   ·   {len(path)} airports",
                         bg=frame.cget("bg"), fg=muted, font=("Segoe UI", 9)).pack(anchor="w", pady=(6, 0))
                def bind_click(widget, index=i):
                    widget.bind("<Button-1>", lambda _e: select_route(index))
                    for child in widget.winfo_children(): bind_click(child, index)
                bind_click(frame)
                state["card_widgets"].append((frame, bar, route_label))
            draw_map()
            self._set_status(f"Compared {len(candidates)} routes: {source} → {target}")

        tk.Button(actions, text="✦  Compare routes", command=compare, bg=green, fg="#E8F6ED",
                  activebackground="#27F0B0", relief="flat", padx=18, pady=9,
                  font=("Segoe UI", 10, "bold"), cursor="hand2").pack(side="left")
        tk.Button(actions, text="↻  Reset", command=lambda: (src.current(0), dst.current(min(1, len(codes)-1)), compare()),
                  bg="#EAF3ED", fg=text, activebackground="#D9F0E1", relief="flat", padx=14, pady=9,
                  font=("Segoe UI", 10), cursor="hand2").pack(side="left", padx=(8, 0))
        map_canvas.bind("<Configure>", draw_map)
        compare()

    def show_visualization(self):
        """Render the airport graph directly in the page; never open a separate image."""
        self.clear_content(); self.page_heading.configure(text="Airport Network")
        bg,panel,muted,green="#F4F7F5","#FFFFFF","#64756A","#14A04B"
        tk.Label(self.content,text="Explore the connection network",bg=bg,fg="#26352B",font=("Segoe UI",15,"bold")).pack(anchor="w")
        tk.Label(self.content,text="The network is drawn from the current airport and route CSV data.",bg=bg,fg=muted,font=("Segoe UI",10)).pack(anchor="w",pady=(3,12))
        card=tk.Frame(self.content,bg=panel,highlightbackground="#BBDCC7",highlightthickness=1,padx=12,pady=12);card.pack(fill="both",expand=True)
        graph=self._graph().G
        canvas=tk.Canvas(card,bg="#EAF3ED",highlightthickness=1,highlightbackground="#DDE8E0",bd=0);canvas.pack(fill="both",expand=True)
        legend=tk.Frame(card,bg=panel);legend.pack(fill="x",pady=(8,0))
        for label,color in [("● Airport","#A9C8E5"),("━ Connection","#C7D2CB"),("━ Shortest path","#14A04B")]:tk.Label(legend,text=label,bg=panel,fg=color,font=("Segoe UI",9,"bold")).pack(side="left",padx=(0,18))
        hint=tk.Label(card,text="Tip: use Shortest Route to highlight a route between two airports.",bg=panel,fg=muted,font=("Segoe UI",9));hint.pack(anchor="w",pady=(8,0))
        def draw(_event=None):
            canvas.delete("all");w=max(canvas.winfo_width(),500);h=max(canvas.winfo_height(),350)
            if graph.number_of_nodes()==0:canvas.create_text(w/2,h/2,text="No airport network data",fill=muted,font=("Segoe UI",11));return
            pos=nx.spring_layout(graph,seed=42,weight="distance_km",iterations=80)
            xs=[v[0] for v in pos.values()];ys=[v[1] for v in pos.values()];pad=42
            coords={n:(pad+(xy[0]-min(xs))/(max(xs)-min(xs) or 1)*(w-2*pad),pad+(xy[1]-min(ys))/(max(ys)-min(ys) or 1)*(h-2*pad)) for n,xy in pos.items()}
            for a,b,d in graph.edges(data=True):
                x1,y1=coords[a];x2,y2=coords[b];canvas.create_line(x1,y1,x2,y2,fill="#C7D2CB",width=2)
                if w>750:canvas.create_text((x1+x2)/2,(y1+y2)/2-7,text=f"{d.get('distance_km',0):,.0f}",fill="#6D98B7",font=("Segoe UI",8))
            for n,(x,y) in coords.items():
                canvas.create_oval(x-7,y-7,x+7,y+7,fill="#EAF3ED",outline="#14A04B",width=2)
                anchor="w" if x<w*.55 else "e";canvas.create_text(x+(11 if anchor=="w" else -11),y-12,text=str(n),anchor=anchor,fill="#26352B",font=("Segoe UI",9,"bold"))
        canvas.bind("<Configure>",draw);draw()
        self._set_status(f"Network visualization: {graph.number_of_nodes()} airports · {graph.number_of_edges()} connections")

    def show_analytics(self):
        """Analytics dashboard with charts embedded in this page, not external files."""
        self.clear_content();self.page_heading.configure(text="Route Analytics")
        bg,panel,muted,blue,green="#F4F7F5","#FFFFFF","#64756A","#168BFF","#14A04B"
        tk.Label(self.content,text="Understand your route network",bg=bg,fg="#26352B",font=("Segoe UI",15,"bold")).pack(anchor="w")
        tk.Label(self.content,text="Statistics and charts are calculated from the current route dataset.",bg=bg,fg=muted,font=("Segoe UI",10)).pack(anchor="w",pady=(3,12))
        routes=self.dm.load_routes().copy();stats=route_statistics(routes)
        if not stats.get("count"):
            tk.Label(self.content,text="No valid route data available yet.",bg=bg,fg=muted,font=("Segoe UI",11)).pack(anchor="w");return
        metrics=tk.Frame(self.content,bg=bg);metrics.pack(fill="x",pady=(0,12))
        for title,value,color in [("TOTAL CONNECTIONS",f"{stats['count']}",blue),("SHORTEST DISTANCE",f"{stats['min']:,.1f} km",green),("LONGEST DISTANCE",f"{stats['max']:,.1f} km","#B79BFF"),("AVERAGE DISTANCE",f"{stats['mean']:,.1f} km","#14A04B"),("MEDIAN DISTANCE",f"{stats['median']:,.1f} km","#FFAD62")]:
            c=tk.Frame(metrics,bg=panel,highlightbackground="#BBDCC7",highlightthickness=1,padx=12,pady=10);c.pack(side="left",fill="both",expand=True,padx=(0,7))
            tk.Label(c,text=title,bg=panel,fg=muted,font=("Segoe UI",8,"bold")).pack(anchor="w")
            tk.Label(c,text=value,bg=panel,fg=color,font=("Segoe UI",14,"bold")).pack(anchor="w",pady=(5,0))
        charts=tk.Frame(self.content,bg=bg);charts.pack(fill="both",expand=True)
        left=tk.Frame(charts,bg=panel,highlightbackground="#BBDCC7",highlightthickness=1,padx=10,pady=10);left.pack(side="left",fill="both",expand=True,padx=(0,8))
        right=tk.Frame(charts,bg=panel,highlightbackground="#BBDCC7",highlightthickness=1,padx=10,pady=10);right.pack(side="left",fill="both",expand=True)
        tk.Label(left,text="Longest route connections",bg=panel,fg="#26352B",font=("Segoe UI",11,"bold")).pack(anchor="w")
        tk.Label(right,text="Distance distribution",bg=panel,fg="#26352B",font=("Segoe UI",11,"bold")).pack(anchor="w")
        bar=tk.Canvas(left,bg=panel,highlightthickness=0,height=300);bar.pack(fill="both",expand=True,pady=(8,0))
        hist=tk.Canvas(right,bg=panel,highlightthickness=0,height=300);hist.pack(fill="both",expand=True,pady=(8,0))
        import pandas as pd
        clean=pd.to_numeric(routes["distance_km"],errors="coerce").dropna()
        top=routes.assign(_distance=pd.to_numeric(routes["distance_km"],errors="coerce")).dropna(subset=["_distance"]).sort_values("_distance",ascending=False).head(7)
        def draw_bar(_event=None):
            bar.delete("all");w=max(bar.winfo_width(),380);h=max(bar.winfo_height(),280);rows=list(top.iterrows())
            if not rows:bar.create_text(w/2,h/2,text="No distance values",fill=muted);return
            labelw=105;rightw=55;usable=max(20,w-labelw-rightw-12);maxv=max(float(r["_distance"]) for _,r in rows) or 1
            step=(h-20)/len(rows)
            for i,(_,r) in enumerate(rows):
                y=12+i*step;name=f"{r['source']} → {r['destination']}";bar.create_text(labelw-7,y+8,text=name,anchor="e",fill=muted,font=("Segoe UI",8))
                bw=usable*float(r["_distance"])/maxv;bar.create_rectangle(labelw,y,labelw+bw,y+15,fill=green if i==0 else blue,outline="")
                bar.create_text(min(labelw+bw+5,w-3),y+8,text=f"{float(r['_distance']):,.0f}",anchor="w",fill="#26352B",font=("Segoe UI",8))
        def draw_hist(_event=None):
            hist.delete("all");w=max(hist.winfo_width(),380);h=max(hist.winfo_height(),280)
            if clean.empty:hist.create_text(w/2,h/2,text="No distance values",fill=muted);return
            edges=[0,500,1000,1500,2000,3000,float("inf")];labels=["0–500","500–1k","1–1.5k","1.5–2k","2–3k","3k+"]
            counts=[int(((clean>=edges[i])&(clean<edges[i+1])).sum()) for i in range(len(labels))];maxc=max(max(counts),1);leftm=28;bottom=h-38;topm=18;plotw=w-leftm-8;ploth=bottom-topm
            for tick in range(maxc+1):
                if maxc>8 and tick%2:continue
                y=bottom-ploth*tick/maxc;hist.create_line(leftm,y,w-6,y,fill="#DDE8E0");hist.create_text(leftm-7,y,text=str(tick),fill=muted,font=("Segoe UI",8))
            gap=plotw/len(counts);bw=gap*.58
            for i,v in enumerate(counts):
                x=leftm+i*gap+(gap-bw)/2;bh=ploth*v/maxc;hist.create_rectangle(x,bottom-bh,x+bw,bottom,fill=blue,outline="")
                hist.create_text(x+bw/2,bottom-bh-9,text=str(v),fill="#26352B",font=("Segoe UI",8,"bold"));hist.create_text(x+bw/2,bottom+13,text=labels[i],fill=muted,font=("Segoe UI",7))
        bar.bind("<Configure>",draw_bar);hist.bind("<Configure>",draw_hist);draw_bar();draw_hist()
        self._set_status("Analytics updated from current route data")

    def run(self):
        self.root.mainloop()
