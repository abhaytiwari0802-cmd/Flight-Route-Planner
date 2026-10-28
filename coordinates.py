"""Airport geographical coordinates database and flight arc path calculations."""
from typing import Dict, Tuple, List
import math
import hashlib

# Preloaded coordinates for known IATA airports (lat, lon)
AIRPORT_COORDINATES: Dict[str, Tuple[float, float]] = {
    # Airports in sample data
    "JFK": (40.6413, -73.7781),     # New York, NY
    "LAX": (33.9416, -118.4085),    # Los Angeles, CA
    "ORD": (41.9742, -87.9073),     # Chicago, IL
    "DFW": (32.8998, -97.0403),     # Dallas/Fort Worth, TX
    "DEN": (39.8561, -104.6737),    # Denver, CO
    "ATL": (33.6407, -84.4277),     # Atlanta, GA
    "SFO": (37.6213, -122.3790),    # San Francisco, CA
    "SEA": (47.4502, -122.3088),    # Seattle, WA
    "MIA": (25.7959, -80.2870),     # Miami, FL
    "BOS": (42.3656, -71.0096),     # Boston, MA
    "PDX": (45.5898, -122.5951),    # Portland, OR
    "LAS": (36.0840, -115.1537),    # Las Vegas, NV
    "EWR": (40.6895, -74.1745),     # Newark, NJ
    "PHX": (33.4352, -112.0101),    # Phoenix, AZ
    "MSP": (44.8848, -93.2223),     # Minneapolis, MN

    # Additional major US and North American Hubs
    "CLT": (35.2140, -80.9431),     # Charlotte, NC
    "MCO": (28.4312, -81.3081),     # Orlando, FL
    "IAH": (29.9902, -95.3368),     # Houston, TX
    "DTW": (42.2162, -83.3554),     # Detroit, MI
    "PHL": (39.8729, -75.2437),     # Philadelphia, PA
    "SLC": (40.7899, -111.9791),    # Salt Lake City, UT
    "BWI": (39.1774, -76.6684),     # Baltimore, MD
    "SAN": (32.7338, -117.1933),    # San Diego, CA
    "TPA": (27.9772, -82.5311),     # Tampa, FL
    "IAD": (38.9531, -77.4565),     # Washington Dulles
    "DCA": (38.8512, -77.0402),     # Washington Reagan
    "MDW": (41.7868, -87.7522),     # Chicago Midway
    "BNA": (36.1263, -86.6774),     # Nashville, TN
    "AUS": (30.1975, -97.6664),     # Austin, TX
    "HNL": (21.3245, -157.9251),    # Honolulu, HI
    "ANC": (61.1760, -149.9984),    # Anchorage, AK
    "YYZ": (43.6777, -79.6248),     # Toronto, Canada
    "YVR": (49.1967, -123.1815),    # Vancouver, Canada

    # Major International Hubs
    "LHR": (51.4700, -0.4543),      # London Heathrow
    "CDG": (49.0097, 2.5479),       # Paris Charles de Gaulle
    "AMS": (52.3105, 4.7683),       # Amsterdam
    "FRA": (50.0379, 8.5622),       # Frankfurt
    "DXB": (25.2532, 55.3657),      # Dubai
    "HND": (35.5494, 139.7798),     # Tokyo Haneda
    "NRT": (35.7720, 140.3929),     # Tokyo Narita
    "SIN": (1.3644, 103.9915),      # Singapore Changi
    "HKG": (22.3080, 113.9185),     # Hong Kong
    "SYD": (-33.9399, 151.1753),    # Sydney
    "DEL": (28.5562, 77.1000),      # Delhi
    "BOM": (19.0896, 72.8656),      # Mumbai
    "BLR": (13.1986, 77.7066),      # Bengaluru
}


def get_airport_coordinates(code: str) -> Tuple[float, float]:
    """Retrieve latitude and longitude for an airport code.
    
    If the airport code is not in the database, generates a deterministic
    coordinate within the continental United States so map plotting never breaks.
    """
    clean_code = str(code).strip().upper()
    if clean_code in AIRPORT_COORDINATES:
        return AIRPORT_COORDINATES[clean_code]
    
    # Deterministic fallback coordinate derived from hash of code
    h = int(hashlib.md5(clean_code.encode()).hexdigest(), 16)
    # Latitude bounded between 28.0 and 46.0 (Continental US)
    lat = 28.0 + (h % 1800) / 100.0
    # Longitude bounded between -120.0 and -75.0 (Continental US)
    lon = -120.0 + ((h >> 16) % 4500) / 100.0
    return round(lat, 4), round(lon, 4)


def calculate_flight_arc(
    start_lat: float, start_lon: float,
    end_lat: float, end_lon: float,
    num_points: int = 40
) -> List[List[float]]:
    """Generate a curved geodesic-like flight arc between two coordinates.
    
    Uses quadratic Bezier curve interpolation with an offset perpendicular
    to the direct path, creating an authentic curved airline trajectory.
    """
    # Midpoint
    mid_lat = (start_lat + end_lat) / 2.0
    mid_lon = (start_lon + end_lon) / 2.0

    # Vector from start to end
    d_lat = end_lat - start_lat
    d_lon = end_lon - start_lon
    dist = math.hypot(d_lat, d_lon)

    if dist < 0.0001:
        return [[start_lat, start_lon], [end_lat, end_lon]]

    # Normal vector perpendicular to trajectory
    # Offset height proportional to distance, with a northern bias
    arc_height = min(max(dist * 0.18, 1.2), 8.0)
    
    # Compute normal vector (-dy, dx)
    norm_lat = -d_lon / dist
    norm_lon = d_lat / dist

    # Adjust control point towards north/convex side
    if norm_lat < 0:
        norm_lat = -norm_lat
        norm_lon = -norm_lon

    ctrl_lat = mid_lat + norm_lat * arc_height
    ctrl_lon = mid_lon + norm_lon * arc_height

    # Generate points along quadratic Bezier curve
    points = []
    for i in range(num_points + 1):
        t = i / float(num_points)
        # B(t) = (1-t)^2 * P0 + 2*(1-t)*t * P1 + t^2 * P2
        b0 = (1.0 - t) ** 2
        b1 = 2.0 * (1.0 - t) * t
        b2 = t ** 2
        
        lat = b0 * start_lat + b1 * ctrl_lat + b2 * end_lat
        lon = b0 * start_lon + b1 * ctrl_lon + b2 * end_lon
        points.append([round(lat, 5), round(lon, 5)])

    return points
