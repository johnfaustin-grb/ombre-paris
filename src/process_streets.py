import osmium as o
import os
import networkx as nx
import logging

WALKABLE_HIGHWAY_TAGS = {
    "residential", "service", "unclassified", "tertiary", "secondary", "primary",
    "living_street", "pedestrian", "track", "road", "footway", "bridleway",
    "steps", "corridor", "path", "cycleway"
}

class StreetGraphHandler(o.SimpleHandler):
    def __init__(self):
        super(StreetGraphHandler, self).__init__()
        self.graph = nx.Graph()

    def node(self, n):
        self.graph.add_node(n.id, lon=n.location.lon, lat=n.location.lat)

    def way(self, w):
        if 'highway' in w.tags and w.tags['highway'] in WALKABLE_HIGHWAY_TAGS:
            nx.add_path(self.graph, [n.ref for n in w.nodes], highway=w.tags['highway'])

def create_street_graph(filepath):
    if not os.path.exists(filepath):
        logging.error(f"OSM file not found at '{filepath}'")
        return None

    logging.info(f"Processing OSM file '{filepath}' to create street graph...")
    handler = StreetGraphHandler()
    handler.apply_file(filepath, locations=True)

    isolated_nodes = [node for node, degree in handler.graph.degree() if degree == 0]
    handler.graph.remove_nodes_from(isolated_nodes)

    logging.info(f"Finished processing OSM file. Graph created with {handler.graph.number_of_nodes()} nodes and {handler.graph.number_of_edges()} edges.")
    return handler.graph

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    osm_file = "monaco.osm.pbf"
    create_street_graph(osm_file)
