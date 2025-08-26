import geopandas as gpd
from shapely.ops import unary_union, nearest_points
from shapely.geometry import LineString, Point
import networkx as nx
from datetime import datetime
import logging
import os

# The shadow calculator is the only utility we need now
from .shadow_calculator import get_sun_position, calculate_shadow_geometry

# --- Configuration ---
PARIS_LAT = 48.8566
PARIS_LON = 2.3522
METRIC_CRS = "EPSG:32631"
WGS84_CRS = "EPSG:4326"

# Paths to pre-processed local data files
GRAPH_PATH = "paris.graphml"
BUILDINGS_PATH = "buildings.feather"
TREES_PATH = "trees.feather"

# --- Global variable to hold the loaded graph ---
# We load this once when the API starts to avoid reloading on every request.
street_graph = None

def load_graph():
    """Loads the street graph from the pre-processed file into a global variable."""
    global street_graph
    if street_graph is None:
        logging.info(f"Loading pre-processed street graph for the first time: {GRAPH_PATH}")
        if not os.path.exists(GRAPH_PATH):
            logging.error(f"Graph file not found: {GRAPH_PATH}. The pre-processing script must be run first.")
            return False
        street_graph = nx.read_graphml(GRAPH_PATH)
        logging.info("Street graph loaded successfully.")
    return True

def find_nearest_node(graph, point_geom_metric):
    nodes_gdf = gpd.GeoDataFrame(geometry=[Point(data['lon'], data['lat']) for _, data in graph.nodes(data=True)], index=graph.nodes())
    nodes_gdf.set_crs(WGS84_CRS, inplace=True)
    nodes_gdf_metric = nodes_gdf.to_crs(METRIC_CRS)
    nearest_node_geom = nearest_points(point_geom_metric, nodes_gdf_metric.unary_union)[1]
    nearest_node_id = list(nodes_gdf_metric.sindex.nearest(nearest_node_geom, return_all=False)[1])[0]
    return nodes_gdf_metric.index[nearest_node_id]

def find_shady_path(start_coords, end_coords, calculation_time):
    logging.info("--- Starting Shady Route Calculation ---")

    # 1. Load all pre-processed data
    logging.info("[Step 1/4] Loading all pre-processed data from local files...")
    if not load_graph(): return None # Load graph if not already loaded

    try:
        buildings_gdf = gpd.read_feather(BUILDINGS_PATH)
        trees_gdf = gpd.read_feather(TREES_PATH)
    except FileNotFoundError as e:
        logging.error(f"Data file not found: {e}. The pre-processing script must be run first.")
        return None

    # 2. Calculate Master Shadow
    logging.info("[Step 2/4] Calculating master shadow polygon...")
    sun_pos = get_sun_position(PARIS_LAT, PARIS_LON, calculation_time)
    buildings_metric = buildings_gdf.to_crs(METRIC_CRS)
    trees_metric = trees_gdf.to_crs(METRIC_CRS)
    trees_metric['canopy_geom'] = trees_metric.apply(lambda r: r.geometry.buffer(r.height / 4), axis=1)
    all_shadows = [calculate_shadow_geometry(b.geometry, b.estimated_height, sun_pos['altitude'], sun_pos['azimuth']) for _, b in buildings_metric.iterrows()]
    all_shadows.extend([calculate_shadow_geometry(t.canopy_geom, t.height, sun_pos['altitude'], sun_pos['azimuth']) for _, t in trees_metric.iterrows()])
    all_shadows = [s for s in all_shadows if s is not None and not s.is_empty]
    master_shadow = unary_union(all_shadows)

    # 3. Weight Street Graph Edges
    logging.info("[Step 3/4] Weighting street graph edges...")
    node_pos = {node: data for node, data in street_graph.nodes(data=True)}
    node_gdf = gpd.GeoDataFrame(geometry=[Point(data['lon'], data['lat']) for data in node_pos.values()], index=node_pos.keys())
    node_gdf.set_crs(WGS84_CRS, inplace=True)
    node_gdf_metric = node_gdf.to_crs(METRIC_CRS)
    for u, v, data in street_graph.edges(data=True):
        segment = LineString([node_gdf_metric.loc[u].geometry, node_gdf_metric.loc[v].geometry])
        data['weight'] = segment.length - segment.intersection(master_shadow).length

    # 4. Find Shaded Path
    logging.info("[Step 4/4] Finding the shadiest path...")
    start_end_gs = gpd.GeoSeries([Point(start_coords[1], start_coords[0]), Point(end_coords[1], end_coords[0])], crs=WGS84_CRS)
    start_end_gs_metric = start_end_gs.to_crs(METRIC_CRS)

    start_node = find_nearest_node(street_graph, start_end_gs_metric.iloc[0])
    end_node = find_nearest_node(street_graph, start_end_gs_metric.iloc[1])
    logging.info(f"Routing from nearest graph node {start_node} to {end_node}")

    try:
        path_node_ids = nx.shortest_path(street_graph, source=start_node, target=end_node, weight='weight')
        path_coords = [(street_graph.nodes[node_id]['lat'], street_graph.nodes[node_id]['lon']) for node_id in path_node_ids]
        return path_coords
    except nx.NetworkXNoPath:
        return None

if __name__ == "__main__":
    print("This script is a module and should be called from the API.")
