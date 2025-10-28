import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import logging

def process_tree_data(url, nrows=None):
    """
    Loads and processes tree data from the Paris Open Data URL.
    """
    logging.info("Streaming tree data...")
    try:
        df = pd.read_csv(url, sep=';', nrows=nrows)
        logging.info(f"Loaded a sample of {len(df)} tree rows.")

        def parse_point(coord_str):
            if isinstance(coord_str, str):
                try:
                    lat, lon = map(float, coord_str.split(','))
                    return Point(lon, lat)
                except (ValueError, TypeError):
                    return None
            return None

        df['geometry'] = df['geo_point_2d'].apply(parse_point)
        df = df.dropna(subset=['geometry'])

        gdf = gpd.GeoDataFrame(df, geometry='geometry')
        gdf.set_crs("EPSG:4326", inplace=True)

        gdf['height'] = pd.to_numeric(gdf['HAUTEUR (m)'], errors='coerce').fillna(0)

        logging.info("Finished processing tree data.")
        return gdf[['geometry', 'height', 'CIRCONFERENCE (cm)', 'LIBELLE FRANCAIS']]

    except Exception as e:
        logging.error(f"An error occurred in process_tree_data: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    TREE_DATA_URL = "https://data.iledefrance.fr/api/explore/v2.1/catalog/datasets/les-arbres/exports/csv?use_labels=true"
    process_tree_data(TREE_DATA_URL, nrows=10)
