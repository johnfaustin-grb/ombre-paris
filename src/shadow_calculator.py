import suncalc
from datetime import datetime, timedelta, timezone
import math
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

# Import the processing functions from our other scripts
from process_buildings import process_building_data
from process_trees import process_tree_data

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
    print("--- Shadow Calculation Proof of Concept ---")

    # 1. Get Sun Position
    paris_tz = timezone(timedelta(hours=2))
    dt_paris = datetime(2025, 8, 25, 14, 0, 0, tzinfo=paris_tz)
    sun_pos = get_sun_position(PARIS_LAT, PARIS_LON, dt_paris)
    print(f"\n1. Sun position calculated for {dt_paris}")

    # 2. Load and process building data
    print("\n2. Loading building data...")
    BUILDING_DATA_URL = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/volumesbatisparis/exports/csv?use_labels=true"
    buildings_gdf = process_building_data(BUILDING_DATA_URL, nrows=100)

    if buildings_gdf is not None and not buildings_gdf.empty:
        # 3. Reproject to a metric CRS
        print(f"\n3. Reprojecting to metric CRS ({METRIC_CRS})...")
        buildings_metric = buildings_gdf.to_crs(METRIC_CRS)

        # 4. Select the TALLEST building in the sample for a better test
        print("\n4. Calculating shadow for the tallest building in the sample...")
        tallest_building = buildings_metric.loc[buildings_metric['estimated_height'].idxmax()]
        building_geom = tallest_building.geometry
        building_height = tallest_building.estimated_height

        print(f"   - Building Height: {building_height:.2f} m")

        shadow = calculate_shadow_geometry(building_geom, building_height, sun_pos['altitude'], sun_pos['azimuth'])

        if shadow:
            print("\n--- Shadow Calculation Result ---")
            print("Original Building Footprint (first 5 coords):")
            print(list(building_geom.exterior.coords)[:5])
            print("\nCalculated Shadow Polygon (first 5 coords):")
            print(list(shadow.exterior.coords)[:5])
            print("---------------------------------")
            print("\nScript finished successfully.")
        else:
            print("Could not calculate shadow.")
    else:
        print("Could not load building data. Aborting.")
