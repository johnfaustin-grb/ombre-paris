import pandas as pd
import geopandas as gpd
import json
from shapely.geometry import shape

def process_building_data(url, nrows=None):
    """
    Loads and processes building data from the Paris Open Data URL.
    - Reads CSV from URL.
    - Parses the embedded JSON in the 'geom' column to create Shapely objects.
    - Creates a GeoDataFrame.
    - Estimates building height based on the number of floors.
    """
    print("Streaming building data from URL...")
    try:
        df = pd.read_csv(url, sep=';', nrows=nrows)
        print(f"Successfully loaded a sample of {len(df)} rows.")

        print("Parsing JSON geometries from 'geom' column...")
        df['geometry'] = df['geom'].apply(lambda x: shape(json.loads(x)) if isinstance(x, str) else None)
        df = df.dropna(subset=['geometry'])

        gdf = gpd.GeoDataFrame(df, geometry='geometry')
        gdf.set_crs("EPSG:4326", inplace=True)

        print("GeoDataFrame created successfully.")

        # Estimate building height
        # H_ET_MAX is the number of floors *above* the ground floor.
        # A building with H_ET_MAX=0 is a single-story building (RDC).
        # We assume total floors = H_ET_MAX + 1, and each floor is 3m high.
        gdf['H_ET_MAX'] = pd.to_numeric(gdf['H_ET_MAX'], errors='coerce').fillna(0)
        gdf['estimated_height'] = (gdf['H_ET_MAX'] + 1) * 3.0

        print("Estimated building heights with new logic.")

        result = gdf[['geometry', 'estimated_height', 'H_ET_MAX', 'L_PLAN_H']]

        print("\nProcessed data sample (first 5 rows):")
        print(result.head())

        return result

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    BUILDING_DATA_URL = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/volumesbatisparis/exports/csv?use_labels=true"

    processed_buildings = process_building_data(BUILDING_DATA_URL, nrows=1000)

    if processed_buildings is not None:
        print(f"\nSuccessfully processed {len(processed_buildings)} buildings.")
        print("\nScript finished successfully.")
    else:
        print("\nScript finished with errors.")
