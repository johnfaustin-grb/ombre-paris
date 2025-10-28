import pandas as pd
import geopandas as gpd
import json
from shapely.geometry import shape
import logging

def process_building_data(url, nrows=None):
    """
    Loads and processes building data from the Paris Open Data URL.
    """
    logging.info("Streaming building data...")
    try:
        df = pd.read_csv(url, sep=';', nrows=nrows)
        logging.info(f"Loaded a sample of {len(df)} building rows.")

        df['geometry'] = df['geom'].apply(lambda x: shape(json.loads(x)) if isinstance(x, str) else None)
        df = df.dropna(subset=['geometry'])

        gdf = gpd.GeoDataFrame(df, geometry='geometry')
        gdf.set_crs("EPSG:4326", inplace=True)

        gdf['H_ET_MAX'] = pd.to_numeric(gdf['H_ET_MAX'], errors='coerce').fillna(0)
        gdf['estimated_height'] = (gdf['H_ET_MAX'] + 1) * 3.0

        logging.info("Finished processing building data.")
        return gdf[['geometry', 'estimated_height', 'H_ET_MAX', 'L_PLAN_H']]

    except Exception as e:
        logging.error(f"An error occurred in process_building_data: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    BUILDING_DATA_URL = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/volumesbatisparis/exports/csv?use_labels=true"
    process_building_data(BUILDING_DATA_URL, nrows=10)
