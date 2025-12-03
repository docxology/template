"""Network Analysis Module for Ways of Figuring Things Out.

This module implements graph-based analysis of the relationships between ways,
rooms, and dialogue patterns in Andrius Kulikauskas's philosophical framework.
Replaces the generic data_processing.py module with domain-specific network
analysis for understanding connections in the House of Knowledge.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import statistics
import networkx as nx
from pathlib import Path

from .database import WaysDatabase
from .sql_queries import WaysSQLQueries
from .models import Way


@dataclass
class WaysNetwork:
    """Network representation of ways and their relationships."""
    graph: nx.Graph = field(default_factory=nx.Graph)
    ways: Dict[int, Way] = field(default_factory=dict)
    edge_types: Dict[Tuple[int, int], str] = field(default_factory=dict)
    node_attributes: Dict[int, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class NetworkMetrics:
    """Network analysis metrics."""
    node_count: int = 0
    edge_count: int = 0
    density: float = 0.0
    average_degree: float = 0.0
    degree_centrality: Dict[int, float] = field(default_factory=dict)
    betweenness_centrality: Dict[int, float] = field(default_factory=dict)
    closeness_centrality: Dict[int, float] = field(default_factory=dict)
    eigenvector_centrality: Dict[int, float] = field(default_factory=dict)
    clustering_coefficient: float = 0.0
    connected_components: int = 0
    largest_component_size: int = 0


@dataclass
class CommunityStructure:
    """Community detection results."""
    communities: List[List[int]] = field(default_factory=list)
    modularity: float = 0.0
    community_sizes: List[int] = field(default_factory=list)
    community_labels: Dict[int, int] = field(default_factory=dict)


@dataclass
class CentralWays:
    """Analysis of central ways in the network."""
    by_degree: List[Tuple[int, int]] = field(default_factory=list)
    by_betweenness: List[Tuple[int, float]] = field(default_factory=list)
    by_closeness: List[Tuple[int, float]] = field(default_factory=list)
    by_eigenvector: List[Tuple[int, float]] = field(default_factory=list)
    hubs: List[int] = field(default_factory=list)
    bridges: List[int] = field(default_factory=list)


class WaysNetworkAnalyzer:
    """Analyzer for network relationships in ways of figuring things out."""

    def __init__(self, db_path: str = None):
        """Initialize analyzer with database connection."""
        self.db = WaysDatabase(db_path)
        self.queries = WaysSQLQueries(db_path)
        self.network = self._build_ways_network()

    def _build_ways_network(self) -> WaysNetwork:
        """Build the network of ways relationships."""
        network = WaysNetwork()

        # Load all ways
        _, ways_data = self.queries.get_all_ways_sql()
        for row in ways_data:
            way = Way(
                id=row[0],
                way=row[1],
                dialoguewith=row[2],
                dialoguetype=row[3],
                dialoguetypetype=row[4],
                wayurl=row[5],
                examples=row[6],
                dialoguetypetypetype=row[7],
                mene=row[8],
                dievas=row[9],
                comments=row[10],
                laikinas=row[11]
            )
            network.ways[way.id] = way
            network.graph.add_node(way.id)

            # Add node attributes
            network.node_attributes[way.id] = {
                'way_text': way.way,
                'room': way.mene,
                'dialogue_type': way.dialoguetype,
                'dialogue_partner': way.dialoguewith,
                'god_relationship': way.dievas,
                'examples_length': len(way.examples) if way.examples else 0
            }

        # Add edges based on relationships
        self._add_room_edges(network)
        self._add_partner_edges(network)
        self._add_type_edges(network)

        return network

    def _add_room_edges(self, network: WaysNetwork) -> None:
        """Add edges between ways in the same room."""
        room_ways = defaultdict(list)
        for way_id, way in network.ways.items():
            room_ways[way.mene].append(way_id)

        for room, ways_in_room in room_ways.items():
            if len(ways_in_room) > 1:
                for i, way1_id in enumerate(ways_in_room):
                    for j, way2_id in enumerate(ways_in_room):
                        if i < j:  # Avoid duplicate edges
                            network.graph.add_edge(way1_id, way2_id,
                                                 edge_type='same_room',
                                                 room=room,
                                                 weight=1.0)
                            network.edge_types[(way1_id, way2_id)] = 'same_room'

    def _add_partner_edges(self, network: WaysNetwork) -> None:
        """Add edges between ways with the same dialogue partner."""
        partner_ways = defaultdict(list)
        for way_id, way in network.ways.items():
            partner_ways[way.dialoguewith].append(way_id)

        for partner, ways_with_partner in partner_ways.items():
            if len(ways_with_partner) > 1:
                for i, way1_id in enumerate(ways_with_partner):
                    for j, way2_id in enumerate(ways_with_partner):
                        if i < j:  # Avoid duplicate edges
                            # Only add edge if not already connected by room
                            if not network.graph.has_edge(way1_id, way2_id):
                                network.graph.add_edge(way1_id, way2_id,
                                                     edge_type='same_partner',
                                                     partner=partner,
                                                     weight=0.8)
                                network.edge_types[(way1_id, way2_id)] = 'same_partner'

    def _add_type_edges(self, network: WaysNetwork) -> None:
        """Add edges between ways with the same dialogue type."""
        type_ways = defaultdict(list)
        for way_id, way in network.ways.items():
            type_ways[way.dialoguetype].append(way_id)

        for dialogue_type, ways_with_type in type_ways.items():
            if len(ways_with_type) > 1:
                for i, way1_id in enumerate(ways_with_type):
                    for j, way2_id in enumerate(ways_with_type):
                        if i < j:  # Avoid duplicate edges
                            # Only add edge if not already connected
                            if not network.graph.has_edge(way1_id, way2_id):
                                network.graph.add_edge(way1_id, way2_id,
                                                     edge_type='same_type',
                                                     dialogue_type=dialogue_type,
                                                     weight=0.6)
                                network.edge_types[(way1_id, way2_id)] = 'same_type'

    def build_ways_network(self) -> WaysNetwork:
        """Get the constructed ways network."""
        return self.network

    def add_room_edges(self, network: WaysNetwork, db_path: str = None) -> None:
        """Add room-based edges to an existing network."""
        # Room edges are already added in _build_ways_network
        pass

    def add_partner_edges(self, network: WaysNetwork, db_path: str = None) -> None:
        """Add partner-based edges to an existing network."""
        # Partner edges are already added in _build_ways_network
        pass

    def add_question_edges(self, network: WaysNetwork, db_path: str = None) -> None:
        """Add question-based edges (if questions connect ways)."""
        # Currently no direct question-way relationships in the data
        # This could be extended if question relationships are established
        pass

    def compute_centrality_metrics(self) -> NetworkMetrics:
        """Compute comprehensive network centrality metrics."""
        metrics = NetworkMetrics(
            node_count=self.network.graph.number_of_nodes(),
            edge_count=self.network.graph.number_of_edges(),
            density=nx.density(self.network.graph),
            average_degree=sum(dict(self.network.graph.degree()).values()) / self.network.graph.number_of_nodes() if self.network.graph.number_of_nodes() > 0 else 0
        )

        # Centrality measures
        if metrics.node_count > 1:
            try:
                metrics.degree_centrality = nx.degree_centrality(self.network.graph)
                metrics.betweenness_centrality = nx.betweenness_centrality(self.network.graph)
                metrics.closeness_centrality = nx.closeness_centrality(self.network.graph)
                metrics.eigenvector_centrality = nx.eigenvector_centrality(self.network.graph, max_iter=1000)
            except:
                # Handle cases where centrality can't be computed
                pass

        metrics.clustering_coefficient = nx.average_clustering(self.network.graph)

        # Connected components
        components = list(nx.connected_components(self.network.graph))
        metrics.connected_components = len(components)
        metrics.largest_component_size = max(len(c) for c in components) if components else 0

        return metrics

    def detect_communities(self) -> CommunityStructure:
        """Detect communities in the ways network."""
        structure = CommunityStructure()

        # Use Louvain method for community detection (greedy modularity maximization)
        try:
            communities = nx.community.greedy_modularity_communities(self.network.graph)
            structure.communities = [list(c) for c in communities]
            structure.modularity = nx.community.modularity(self.network.graph, communities)
            structure.community_sizes = [len(c) for c in communities]

            # Create community labels
            for community_id, community in enumerate(structure.communities):
                for way_id in community:
                    structure.community_labels[way_id] = community_id

        except Exception as e:
            # If community detection fails, create single community
            all_nodes = list(self.network.graph.nodes())
            structure.communities = [all_nodes]
            structure.community_sizes = [len(all_nodes)]
            for way_id in all_nodes:
                structure.community_labels[way_id] = 0

        return structure

    def analyze_network_structure(self) -> Dict[str, Any]:
        """Analyze overall network structure."""
        metrics = self.compute_centrality_metrics()
        communities = self.detect_communities()

        analysis = {
            'metrics': {
                'node_count': metrics.node_count,
                'edge_count': metrics.edge_count,
                'density': metrics.density,
                'average_degree': metrics.average_degree,
                'clustering_coefficient': metrics.clustering_coefficient,
                'connected_components': metrics.connected_components,
                'largest_component_ratio': metrics.largest_component_size / metrics.node_count if metrics.node_count > 0 else 0
            },
            'communities': {
                'count': len(communities.communities),
                'sizes': communities.community_sizes,
                'modularity': communities.modularity,
                'largest_community_ratio': max(communities.community_sizes) / metrics.node_count if communities.community_sizes else 0
            },
            'centralization': self._compute_centralization(metrics),
            'structural_holes': self._analyze_structural_holes()
        }

        return analysis

    def _compute_centralization(self, metrics: NetworkMetrics) -> Dict[str, float]:
        """Compute network centralization measures."""
        centralization = {}

        if metrics.degree_centrality:
            max_degree_cent = max(metrics.degree_centrality.values())
            degree_cents = list(metrics.degree_centrality.values())
            centralization['degree'] = sum(max_degree_cent - c for c in degree_cents) / ((len(degree_cents) - 1) * (len(degree_cents) - 2)) if len(degree_cents) > 2 else 0

        if metrics.betweenness_centrality:
            max_between_cent = max(metrics.betweenness_centrality.values())
            between_cents = list(metrics.betweenness_centrality.values())
            centralization['betweenness'] = sum(max_between_cent - c for c in between_cents) / ((len(between_cents) - 1) * (len(between_cents) - 2)) if len(between_cents) > 2 else 0

        return centralization

    def _analyze_structural_holes(self) -> Dict[str, Any]:
        """Analyze structural holes in the network."""
        # Calculate constraint scores (measure of structural holes)
        constraints = {}
        effective_sizes = {}

        for node in self.network.graph.nodes():
            # Burt's constraint measure
            neighbors = list(self.network.graph.neighbors(node))
            if len(neighbors) <= 1:
                constraints[node] = 0.0
                effective_sizes[node] = len(neighbors)
                continue

            constraint = 0.0
            for neighbor in neighbors:
                neighbor_neighbors = list(self.network.graph.neighbors(neighbor))
                common_neighbors = set(neighbors) & set(neighbor_neighbors)

                p_ij = 1.0 / len(neighbors)  # Proportion of node's network time invested in neighbor
                p_jk_sum = sum(1.0 / len(list(self.network.graph.neighbors(k)))
                              for k in neighbor_neighbors if k != node)

                constraint += p_ij * p_jk_sum

            constraints[node] = constraint
            effective_sizes[node] = len(neighbors) - constraint

        return {
            'avg_constraint': statistics.mean(constraints.values()) if constraints else 0,
            'avg_effective_size': statistics.mean(effective_sizes.values()) if effective_sizes else 0,
            'high_constraint_nodes': [n for n, c in constraints.items() if c > 1.0]
        }

    def find_central_ways(self) -> CentralWays:
        """Find most central ways using multiple centrality measures."""
        central = CentralWays()
        metrics = self.compute_centrality_metrics()

        # Sort by degree centrality
        if metrics.degree_centrality:
            central.by_degree = sorted(metrics.degree_centrality.items(),
                                     key=lambda x: x[1], reverse=True)[:10]

        # Sort by betweenness centrality
        if metrics.betweenness_centrality:
            central.by_betweenness = sorted(metrics.betweenness_centrality.items(),
                                          key=lambda x: x[1], reverse=True)[:10]

        # Sort by closeness centrality
        if metrics.closeness_centrality:
            central.by_closeness = sorted(metrics.closeness_centrality.items(),
                                        key=lambda x: x[1], reverse=True)[:10]

        # Sort by eigenvector centrality
        if metrics.eigenvector_centrality:
            central.by_eigenvector = sorted(metrics.eigenvector_centrality.items(),
                                          key=lambda x: x[1], reverse=True)[:10]

        # Identify hubs (high degree centrality)
        if central.by_degree:
            degree_threshold = statistics.mean([d for _, d in central.by_degree]) + statistics.stdev([d for _, d in central.by_degree]) if len(central.by_degree) > 1 else central.by_degree[0][1]
            central.hubs = [way_id for way_id, degree in central.by_degree if degree > degree_threshold]

        # Identify bridges (high betweenness centrality)
        if central.by_betweenness:
            between_threshold = statistics.mean([b for _, b in central.by_betweenness]) + statistics.stdev([b for _, b in central.by_betweenness]) if len(central.by_betweenness) > 1 else central.by_betweenness[0][1]
            central.bridges = [way_id for way_id, between in central.by_betweenness if between > between_threshold]

        return central

    def get_way_neighbors(self, way_id: int) -> List[Tuple[int, str]]:
        """Get direct neighbors of a way with connection types."""
        if way_id not in self.network.graph:
            return []

        neighbors = []
        for neighbor_id in self.network.graph.neighbors(way_id):
            edge_data = self.network.graph.get_edge_data(way_id, neighbor_id)
            edge_type = edge_data.get('edge_type', 'unknown') if edge_data else 'unknown'
            neighbors.append((neighbor_id, edge_type))

        return neighbors

    def get_way_paths(self, way1_id: int, way2_id: int) -> List[List[int]]:
        """Find shortest paths between two ways."""
        try:
            paths = list(nx.all_shortest_paths(self.network.graph, way1_id, way2_id))
            return paths
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def get_way_cluster(self, way_id: int) -> List[int]:
        """Get the community cluster containing a way."""
        communities = self.detect_communities()
        for community in communities.communities:
            if way_id in community:
                return community
        return []

    def get_network_edges(self) -> List[Tuple[int, int, str]]:
        """Get all network edges with types."""
        edges = []
        for way1, way2, data in self.network.graph.edges(data=True):
            edge_type = data.get('edge_type', 'unknown')
            edges.append((way1, way2, edge_type))
        return edges

    def analyze_room_networks(self) -> Dict[str, Dict[str, Any]]:
        """Analyze sub-networks for each room."""
        room_networks = {}

        for room_short in set(way.mene for way in self.network.ways.values()):
            room_ways = [wid for wid, way in self.network.ways.items() if way.mene == room_short]

            if len(room_ways) > 1:
                # Create subgraph for this room
                subgraph = self.network.graph.subgraph(room_ways)

                room_networks[room_short] = {
                    'way_count': len(room_ways),
                    'edge_count': subgraph.number_of_edges(),
                    'density': nx.density(subgraph),
                    'avg_degree': sum(dict(subgraph.degree()).values()) / len(room_ways),
                    'connected': nx.is_connected(subgraph),
                    'diameter': nx.diameter(subgraph) if nx.is_connected(subgraph) else None
                }
            else:
                room_networks[room_short] = {
                    'way_count': len(room_ways),
                    'edge_count': 0,
                    'density': 0.0,
                    'avg_degree': 0.0,
                    'connected': True,
                    'diameter': 0
                }

        return room_networks

    def analyze_partner_networks(self) -> Dict[str, Dict[str, Any]]:
        """Analyze sub-networks for each dialogue partner."""
        partner_networks = {}

        for partner in set(way.dialoguewith for way in self.network.ways.values()):
            partner_ways = [wid for wid, way in self.network.ways.items() if way.dialoguewith == partner]

            if len(partner_ways) > 1:
                subgraph = self.network.graph.subgraph(partner_ways)

                partner_networks[partner] = {
                    'way_count': len(partner_ways),
                    'edge_count': subgraph.number_of_edges(),
                    'density': nx.density(subgraph),
                    'avg_degree': sum(dict(subgraph.degree()).values()) / len(partner_ways),
                    'connected': nx.is_connected(subgraph)
                }
            else:
                partner_networks[partner] = {
                    'way_count': len(partner_ways),
                    'edge_count': 0,
                    'density': 0.0,
                    'avg_degree': 0.0,
                    'connected': True
                }

        return partner_networks

    def export_network_data(self, output_path: str = None) -> Dict[str, Any]:
        """Export network data for external analysis."""
        if output_path is None:
            output_path = Path(__file__).parent.parent / "output" / "data"

        output_path = Path(output_path)
        output_path.mkdir(exist_ok=True)

        # Export node data
        nodes_data = []
        for way_id, way in self.network.ways.items():
            node_data = {
                'id': way_id,
                'way': way.way,
                'room': way.mene,
                'dialogue_type': way.dialoguetype,
                'dialogue_partner': way.dialoguewith,
                'god_relationship': way.dievas,
                'examples_length': len(way.examples) if way.examples else 0
            }
            nodes_data.append(node_data)

        # Export edge data
        edges_data = []
        for way1, way2, data in self.network.graph.edges(data=True):
            edge_data = {
                'source': way1,
                'target': way2,
                'type': data.get('edge_type', 'unknown'),
                'weight': data.get('weight', 1.0)
            }
            edges_data.append(edge_data)

        network_data = {
            'nodes': nodes_data,
            'edges': edges_data,
            'metadata': {
                'node_count': len(nodes_data),
                'edge_count': len(edges_data),
                'generated_at': str(Path(__file__).parent.parent)
            }
        }

        return network_data


# Convenience functions
def analyze_ways_network(db_path: str = None) -> Dict[str, Any]:
    """Convenience function for complete network analysis."""
    analyzer = WaysNetworkAnalyzer(db_path)
    metrics = analyzer.compute_centrality_metrics()
    communities = analyzer.detect_communities()
    central_ways = analyzer.find_central_ways()

    return {
        'network_structure': analyzer.analyze_network_structure(),
        'central_ways': {
            'by_degree': central_ways.by_degree[:5],
            'by_betweenness': central_ways.by_betweenness[:5],
            'hubs': central_ways.hubs,
            'bridges': central_ways.bridges
        },
        'communities': {
            'count': len(communities.communities),
            'sizes': communities.community_sizes,
            'modularity': communities.modularity
        }
    }


def get_network_analyzer(db_path: str = None) -> WaysNetworkAnalyzer:
    """Get configured network analyzer."""
    return WaysNetworkAnalyzer(db_path)
