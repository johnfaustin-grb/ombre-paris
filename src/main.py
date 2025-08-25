import geopandas as gpd
from shapely.ops import unary_union, nearest_points
from shapely.geometry import LineString, Point
import networkx as nx
from datetime import datetime
import logging

# Use relative imports for modules within the same 'src' package
from .process_streets import create_street_graph
from .process_buildings import process_building_data
from .process_trees import process_tree_data
from .shadow_calculator import get_sun_position, calculate_shadow_geometry

# --- Configuration ---
PARIS_LAT = 48.8566
PARIS_LON = 2.3522
METRIC_CRS = "EPSG:32631"
WGS84_CRS = "EPSG:4326"
OSM_DATA_FILE = "monaco.osm.pbf"
BUILDING_DATA_URL = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/volumesbatisparis/exports/csv?use_labels=true"
TREE_DATA_URL = "https://data.iledefrance.fr/api/explore/v2.1/catalog/datasets/les-arbres/exports/csv?use_labels=true"
SAMPLE_SIZE = 200

def find_nearest_node(graph, point_geom_metric):
    nodes_gdf = gpd.GeoDataFrame(geometry=[Point(data['lon'], data['lat']) for _, data in graph.nodes(data=True)], index=graph.nodes())
    nodes_gdf.set_crs(WGS84_CRS, inplace=True)
    nodes_gdf_metric = nodes_gdf.to_crs(METRIC_CRS)
    nearest_node_geom = nearest_points(point_geom_metric, nodes_gdf_metric.unary_union)[1]
    nearest_node_id = list(nodes_gdf_metric.sindex.nearest(nearest_node_geom, return_all=False)[1])[0]
    return nodes_gdf_metric.index[nearest_node_id]

def find_shady_path(start_coords, end_coords, calculation_time):
    logging.info("--- Starting Shady Route Calculation ---")

    logging.info(f"\n[Step 1/4] Loading data...")
    street_graph = create_street_graph(OSM_DATA_FILE)
    buildings_gdf = process_building_data(BUILDING_DATA_URL, nrows=SAMPLE_SIZE)
    trees_gdf = process_tree_data(TREE_DATA_URL, nrows=SAMPLE_SIZE)
    if not all([street_graph, buildings_gdf is not None, trees_gdf is not None]): return None

    logging.info("\n[Step 2/4] Calculating master shadow polygon...")
    sun_pos = get_sun_position(PARIS_LAT, PARIS_LON, calculation_time)
    buildings_metric = buildings_gdf.to_crs(METRIC_CRS)
    trees_metric = trees_gdf.to_crs(METRIC_CRS)
    trees_metric['canopy_geom'] = trees_metric.apply(lambda r: r.geometry.buffer(r.height / 4), axis=1)
    all_shadows = [calculate_shadow_geometry(b.geometry, b.estimated_height, sun_pos['altitude'], sun_pos['azimuth']) for _, b in buildings_metric.iterrows()]
    all_shadows.extend([calculate_shadow_geometry(t.canopy_geom, t.height, sun_pos['altitude'], sun_pos['azimuth']) for _, t in trees_metric.iterrows()])
    all_shadows = [s for s in all_shadows if s is not None and not s.is_empty]
    master_shadow = unary_union(all_shadows)

    logging.info("\n[Step 3/4] Weighting street graph edges...")
    node_pos = {node: data for node, data in street_graph.nodes(data=True)}
    node_gdf = gpd.GeoDataFrame(geometry=[Point(data['lon'], data['lat']) for data in node_pos.values()], index=node_pos.keys())
    node_gdf.set_crs(WGS84_CRS, inplace=True)
    node_gdf_metric = node_gdf.to_crs(METRIC_CRS)
    for u, v, data in street_graph.edges(data=True):
        segment = LineString([node_gdf_metric.loc[u].geometry, node_gdf_metric.loc[v].geometry])
        data['weight'] = segment.length - segment.intersection(master_shadow).length

    logging.info("\n[Step 4/4] Finding the shadiest path...")
    start_end_gs = gpd.GeoSeries([Point(start_coords[1], start_coords[0]), Point(end_coords[1], end_coords[0])], crs=WGS84_CRS)
    start_end_gs_metric = start_end_gs.to_crs(METRIC_CRS)

    start_node = find_nearest_node(street_graph, start_end_gs_metric.iloc[0])
    end_node = find_nearest_node(street_graph, start_end_gs_metric.iloc[1])
    logging.info(f"Routing from nearest graph node {start_node} to {end_node}")

    try:
        path_node_ids = nx.shortest_path(street_graph, source=start_node, target=end_node, weight='weight')
        path_coords = [(node_pos[node_id]['lat'], node_pos[node_id]['lon']) for node_id in path_node_ids]
        return path_coords
    except nx.NetworkXNoPath:
        return None

if __name__ == "__main__":
    # To test this module standalone, we need to set up logging
    logging.basicConfig(level=logging.INFO)
    from datetime import datetime, timedelta, timezone
    start_point = (43.73, 7.42)
    end_point = (43.74, 7.43)
    paris_tz = timezone(timedelta(hours=2))
    test_time = datetime(2025, 8, 25, 14, 0, 0, tzinfo=paris_tz)
    shady_path = find_shady_path(start_point, end_point, test_time)
    if shady_path:
        logging.info("\n--- Shady Route Found! ---")
        logging.info(f"Path consists of {len(shady_path)} points.")
        logging.info(f"First 5 points: {shady_path[:5]}")
    else:
        logging.info("Could not find a shady route.")
