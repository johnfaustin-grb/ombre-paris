import os
import sys
import logging
import networkx as nx
import requests
import pandas as pd

# Add the parent directory ('..') to the Python path to allow importing from 'src'
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.process_streets import create_street_graph
from src.process_buildings import process_building_data
from src.process_trees import process_tree_data

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def download_file(url, local_filename):
    """Downloads a file from a URL to a local path."""
    logging.info(f"Downloading {url} to {local_filename}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logging.info(f"Successfully downloaded {local_filename}.")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download {url}: {e}")
        return False

def main():
    """
    Main function to run the entire pre-processing pipeline.
    Downloads all necessary data and processes it into optimized local files.
    """
    # --- Configuration ---
    STREET_DATA_URL = "https://download.geofabrik.de/europe/france/ile-de-france-latest.osm.pbf"
    BUILDING_DATA_URL = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/volumesbatisparis/exports/csv?use_labels=true"
    TREE_DATA_URL = "https://data.iledefrance.fr/api/explore/v2.1/catalog/datasets/les-arbres/exports/csv?use_labels=true"

    PBF_LOCAL_PATH = "paris_temp.osm.pbf"
    BUILDING_LOCAL_PATH = "buildings_temp.csv"
    TREE_LOCAL_PATH = "trees_temp.csv"

    GRAPH_OUTPUT_PATH = "paris.graphml"
    BUILDING_OUTPUT_PATH = "buildings.feather"
    TREE_OUTPUT_PATH = "trees.feather"

    # --- Execution ---

    # 1. Download all data
    logging.info("--- Step 1/3: Downloading all source data ---")
    if not download_file(STREET_DATA_URL, PBF_LOCAL_PATH): return
    if not download_file(BUILDING_DATA_URL, BUILDING_LOCAL_PATH): return
    if not download_file(TREE_DATA_URL, TREE_LOCAL_PATH): return

    # 2. Process all data
    logging.info("--- Step 2/3: Processing data and saving to optimized formats ---")

    # Process streets
    graph = create_street_graph(PBF_LOCAL_PATH)
    if graph:
        nx.write_graphml(graph, GRAPH_OUTPUT_PATH)
        logging.info(f"Street graph saved to {GRAPH_OUTPUT_PATH}")

    # Process buildings
    buildings_gdf = process_building_data(BUILDING_LOCAL_PATH)
    if buildings_gdf is not None:
        buildings_gdf.to_feather(BUILDING_OUTPUT_PATH)
        logging.info(f"Building data saved to {BUILDING_OUTPUT_PATH}")

    # Process trees
    trees_gdf = process_tree_data(TREE_LOCAL_PATH)
    if trees_gdf is not None:
        trees_gdf.to_feather(TREE_OUTPUT_PATH)
        logging.info(f"Tree data saved to {TREE_OUTPUT_PATH}")

    # 3. Clean up large temporary files
    logging.info("--- Step 3/3: Cleaning up temporary download files ---")
    os.remove(PBF_LOCAL_PATH)
    os.remove(BUILDING_LOCAL_PATH)
    os.remove(TREE_LOCAL_PATH)

    logging.info("Pre-processing complete!")

if __name__ == "__main__":
    main()
