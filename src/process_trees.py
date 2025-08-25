import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

def process_tree_data(url, nrows=None):
    """
    Loads and processes tree data from the Paris Open Data URL.
    - Reads CSV from URL.
    - Parses the 'geo_point_2d' column to create Shapely Point objects.
    - Creates a GeoDataFrame.
    - Cleans the height column.
    """
    print("Streaming tree data from URL...")
    try:
        df = pd.read_csv(url, sep=';', nrows=nrows)
        print(f"Successfully loaded a sample of {len(df)} rows.")

        # The geometry is in the 'geo_point_2d' column as 'lat, lon'
        print("Parsing point geometries from 'geo_point_2d' column...")

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

        print("GeoDataFrame for trees created successfully.")

        # Clean up height column
        gdf['height'] = pd.to_numeric(gdf['HAUTEUR (m)'], errors='coerce').fillna(0)

        print("Cleaned tree height data.")

        result = gdf[['geometry', 'height', 'CIRCONFERENCE (cm)', 'LIBELLE FRANCAIS']]

        print("\nProcessed tree data sample (first 5 rows):")
        print(result.head())

        return result

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    TREE_DATA_URL = "https://data.iledefrance.fr/api/explore/v2.1/catalog/datasets/les-arbres/exports/csv?use_labels=true"

    processed_trees = process_tree_data(TREE_DATA_URL, nrows=1000)

    if processed_trees is not None:
        print(f"\nSuccessfully processed {len(processed_trees)} trees.")
        print("\nScript finished successfully.")
    else:
        print("\nScript finished with errors.")
