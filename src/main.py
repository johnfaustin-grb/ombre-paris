import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import LineString, Point
import networkx as nx
from datetime import datetime, timedelta, timezone
import math
import random

# Import our processing and calculation scripts
from process_streets import create_street_graph
from process_buildings import process_building_data
from process_trees import process_tree_data
from shadow_calculator import get_sun_position, calculate_shadow_geometry

# --- Configuration ---
PARIS_LAT = 48.8566
PARIS_LON = 2.3522
METRIC_CRS = "EPSG:32631"
OSM_DATA_FILE = "monaco.osm.pbf"
BUILDING_DATA_URL = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/volumesbatisparis/exports/csv?use_labels=true"
TREE_DATA_URL = "https://data.iledefrance.fr/api/explore/v2.1/catalog/datasets/les-arbres/exports/csv?use_labels=true"
SAMPLE_SIZE = 500 # Number of buildings/trees to sample for the PoC

def main():
    print("--- Starting Shady Route Finder Proof of Concept ---")

    # === 1. Load Data ===
    print(f"\n[Step 1/4] Loading data (street graph, {SAMPLE_SIZE} buildings, {SAMPLE_SIZE} trees)...")
    street_graph = create_street_graph(OSM_DATA_FILE)
    buildings_gdf = process_building_data(BUILDING_DATA_URL, nrows=SAMPLE_SIZE)
    trees_gdf = process_tree_data(TREE_DATA_URL, nrows=SAMPLE_SIZE)
    if not all([street_graph, buildings_gdf is not None, trees_gdf is not None]): return

    # === 2. Calculate Master Shadow ===
    print("\n[Step 2/4] Calculating master shadow polygon...")
    paris_tz = timezone(timedelta(hours=2))
    dt_paris = datetime(2025, 8, 25, 14, 0, 0, tzinfo=paris_tz)
    sun_pos = get_sun_position(PARIS_LAT, PARIS_LON, dt_paris)

    buildings_metric = buildings_gdf.to_crs(METRIC_CRS)
    trees_metric = trees_gdf.to_crs(METRIC_CRS)
    trees_metric['canopy_geom'] = trees_metric.apply(lambda r: r.geometry.buffer(r.height / 4), axis=1)

    all_shadows = [calculate_shadow_geometry(b.geometry, b.estimated_height, sun_pos['altitude'], sun_pos['azimuth']) for _, b in buildings_metric.iterrows()]
    all_shadows.extend([calculate_shadow_geometry(t.canopy_geom, t.height, sun_pos['altitude'], sun_pos['azimuth']) for _, t in trees_metric.iterrows()])
    all_shadows = [s for s in all_shadows if s is not None and not s.is_empty]

    master_shadow = unary_union(all_shadows)
    print(f"Master shadow created from {len(all_shadows)} objects.")

    # === 3. Weight Street Graph Edges ===
    print("\n[Step 3/4] Weighting street graph edges by sun exposure...")
    node_pos = {node: data for node, data in street_graph.nodes(data=True)}

    # Project node coordinates once
    node_gdf = gpd.GeoDataFrame(geometry=[Point(data['lon'], data['lat']) for data in node_pos.values()], index=node_pos.keys())
    node_gdf.set_crs("EPSG:4326", inplace=True)
    node_gdf_metric = node_gdf.to_crs(METRIC_CRS)

    for u, v, data in street_graph.edges(data=True):
        start_node = node_gdf_metric.loc[u].geometry
        end_node = node_gdf_metric.loc[v].geometry
        segment = LineString([start_node, end_node])

        total_length = segment.length
        shaded_length = segment.intersection(master_shadow).length

        # Weight is the length of the segment exposed to the sun
        data['weight'] = total_length - shaded_length

    print("Finished weighting edges.")

    # === 4. Find Shaded Path ===
    print("\n[Step 4/4] Finding the shadiest path...")
    # Select two random nodes for start and end
    start_node, end_node = random.sample(list(street_graph.nodes), 2)
    print(f"Route from node {start_node} to {end_node}")

    try:
        shady_path = nx.shortest_path(street_graph, source=start_node, target=end_node, weight='weight')
        print("\n--- Shady Route Found! ---")
        print(f"Path consists of {len(shady_path)} nodes:")
        print(shady_path)
    except nx.NetworkXNoPath:
        print(f"No path could be found between {start_node} and {end_node}.")

    print("\n\n--- Proof of Concept Finished ---")

if __name__ == "__main__":
    main()
