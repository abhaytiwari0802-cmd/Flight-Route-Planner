# Flight Route Planner — CustomTkinter Dark Dashboard

This version applies the requested dark navy dashboard theme to this Flight Route Planner desktop app only. It uses CustomTkinter, keeps airport and route records in `data/airports.csv` and `data/routes.csv`, and calculates shortest paths with the existing Dijkstra implementation.

## Run in PyCharm

1. Extract the ZIP and open the extracted folder in PyCharm.
2. Select your project Python interpreter.
3. In the PyCharm terminal, run:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Run `main.py`.

Or from a terminal in the project root:

```bash
python main.py
```

The window starts at 1280×720 and can be resized (minimum 1100×650).

## UI and data

- `src/customtkinter_gui.py` — CustomTkinter UI and canvas charts/network drawing.
- `src/data_manager.py` — CSV loading and persistence.
- `src/route_algorithms.py` — Dijkstra and route helpers.
- `data/airports.csv` — airport code, name, city.
- `data/routes.csv` — source, destination, distance (km), travel time (minutes).

The sample airport network is simulated, not live airline data. The `Airports` and `Routes` sidebar items display the data currently loaded from CSV.


### Network map layout update

The network visualization uses a deterministic force-directed layout so airport nodes are distributed organically in a wide, two-dimensional arrangement rather than a straight line or fixed grid.
