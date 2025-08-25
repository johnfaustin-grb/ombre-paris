import osmium as o
import os
import networkx as nx

WALKABLE_HIGHWAY_TAGS = {
    "residential", "service", "unclassified", "tertiary", "secondary", "primary",
    "living_street", "pedestrian", "track", "road", "footway", "bridleway",
    "steps", "corridor", "path", "cycleway"
}

class StreetGraphHandler(o.SimpleHandler):
    """
    Osmium handler that builds a networkx graph from OSM data.
    """
    def __init__(self):
        super(StreetGraphHandler, self).__init__()
        self.graph = nx.Graph()

    def node(self, n):
        """
        Stores node positions.
        """
        self.graph.add_node(n.id, lon=n.location.lon, lat=n.location.lat)

    def way(self, w):
        """
        Adds edges to the graph for walkable/cyclable ways.
        """
        if 'highway' in w.tags and w.tags['highway'] in WALKABLE_HIGHWAY_TAGS:
            # Add edges between consecutive nodes in the way
            nx.add_path(self.graph, [n.ref for n in w.nodes], highway=w.tags['highway'])

def create_street_graph(filepath):
    """
    Processes an OSM PBF file and returns a networkx graph.
    """
    if not os.path.exists(filepath):
        print(f"Error: File not found at '{filepath}'")
        return None

    print(f"Processing OSM file '{filepath}' to create street graph...")
    handler = StreetGraphHandler()

    # Osmium processes nodes before ways, so this approach works in a single pass.
    # The node method is called for all nodes, then the way method for all ways.
    handler.apply_file(filepath, locations=True)

    # The handler's graph is now populated.
    # We might have isolated nodes that are not part of any way, let's remove them.
    isolated_nodes = [node for node, degree in handler.graph.degree() if degree == 0]
    handler.graph.remove_nodes_from(isolated_nodes)

    print(f"Finished processing. Graph created with:")
    print(f"  - {handler.graph.number_of_nodes()} nodes")
    print(f"  - {handler.graph.number_of_edges()} edges")

    return handler.graph

if __name__ == "__main__":
    osm_file = "monaco.osm.pbf"
    street_graph = create_street_graph(osm_file)

    if street_graph:
        # Print info about a few nodes to verify
        print("\n--- Graph Verification ---")
        node_samples = list(street_graph.nodes(data=True))[:5]
        for node_data in node_samples:
            print(f"Node {node_data[0]}: Lon={node_data[1]['lon']:.4f}, Lat={node_data[1]['lat']:.4f}")

        edge_samples = list(street_graph.edges(data=True))[:5]
        for edge_data in edge_samples:
            print(f"Edge from {edge_data[0]} to {edge_data[1]} (type: {edge_data[2]['highway']})")

        print("\nScript finished successfully.")
    else:
        print("\nScript finished with errors.")
