import suncalc
from datetime import datetime
import math
import geopandas as gpd
from shapely.geometry import Polygon
import logging

# Use relative imports for modules within the same 'src' package
from .process_buildings import process_building_data
from .process_trees import process_tree_data

# --- Configuration ---
PARIS_LAT = 48.8566
PARIS_LON = 2.3522
METRIC_CRS = "EPSG:32631"

def get_sun_position(lat, lon, dt):
    """Calculates the sun's position for a given location and time."""
    position = suncalc.get_position(dt, lon, lat)
    position['azimuth'] = (position['azimuth'] + math.pi) % (2 * math.pi)
    return position

def calculate_shadow_geometry(geometry, height, sun_altitude_rad, sun_azimuth_rad):
    """
    Calculates the 2D shadow polygon for a single geometry.
    """
    if sun_altitude_rad <= 0:
        return None

    shadow_factor = height / math.tan(sun_altitude_rad)
    dx = -math.sin(sun_azimuth_rad) * shadow_factor
    dy = -math.cos(sun_azimuth_rad) * shadow_factor

    def project_coords(coords):
        return [(x + dx, y + dy) for x, y in coords]

    if isinstance(geometry, Polygon):
        return Polygon(project_coords(geometry.exterior.coords))
    return None

if __name__ == "__main__":
    logging.info("This script is a module. Run main.py to test its functionality.")
