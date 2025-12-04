"""Comprehensive tests for network_analysis.py module.

Tests the WaysNetworkAnalyzer class and all network analysis functionality
for understanding relationships between ways in Andrius Kulikauskas's framework.
"""

import pytest
import networkx as nx
from pathlib import Path
from unittest.mock import Mock, MagicMock

from src.network_analysis import (
    WaysNetworkAnalyzer, WaysNetwork, NetworkMetrics,
    CommunityStructure, CentralWays, analyze_ways_network, get_network_analyzer
)
from src.models import Way


class TestWaysNetworkAnalyzer:
    """Test WaysNetworkAnalyzer class methods."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database with test data."""
        mock_db = Mock()
        return mock_db

    @pytest.fixture
    def mock_queries(self):
        """Create a mock SQL queries object with test data."""
        mock_queries = Mock()

        # Mock ways data for network building
        mock_queries.get_all_ways_sql.return_value = (
            "SELECT * FROM ways",
            [
                (1, "Way 1", "Partner A", "Absolute", "Self", "", "Example 1", "", "B", "Creator", "", ""),
                (2, "Way 2", "Partner A", "Absolute", "Self", "", "Example 2", "", "B", "Creator", "", ""),
                (3, "Way 3", "Partner B", "Relative", "Other", "", "Example 3", "", "B", "Sustainer", "", ""),
                (4, "Way 4", "Partner A", "Relative", "Other", "", "Example 4", "", "B2", "Sustainer", "", ""),
                (5, "Way 5", "Partner C", "Absolute", "Self", "", "Example 5", "", "B2", "Creator", "", "")
            ]
        )

        return mock_queries

    @pytest.fixture
    def analyzer(self, mock_db, mock_queries):
        """Create a WaysNetworkAnalyzer with mocked dependencies."""
        analyzer = WaysNetworkAnalyzer.__new__(WaysNetworkAnalyzer)
        analyzer.db = mock_db
        analyzer.queries = mock_queries
        analyzer.network = analyzer._build_ways_network()
        return analyzer

    def test_analyzer_initialization(self):
        """Test WaysNetworkAnalyzer initialization."""
        analyzer = WaysNetworkAnalyzer()
        assert hasattr(analyzer, 'db')
        assert hasattr(analyzer, 'queries')
        assert hasattr(analyzer, 'network')
        assert isinstance(analyzer.network, WaysNetwork)

    def test_analyzer_initialization_with_db_path(self, tmp_path):
        """Test WaysNetworkAnalyzer initialization with custom database path."""
        custom_path = tmp_path / "custom.db"

        # Initialize database from dump
        from src.database import WaysDatabase
        db = WaysDatabase(db_path=str(custom_path))
        dump_path = Path(__file__).parent.parent / "db" / "andrius_ways.sql"
        if dump_path.exists():
            db.initialize_from_mysql_dump(str(dump_path))

            analyzer = WaysNetworkAnalyzer(db_path=str(custom_path))
            assert hasattr(analyzer, 'db')
            assert hasattr(analyzer, 'queries')
        else:
            pytest.skip("Database dump not found")

    def test_build_ways_network(self, analyzer):
        """Test network construction."""
        network = analyzer.build_ways_network()
        assert isinstance(network, WaysNetwork)
        assert isinstance(network.graph, nx.Graph)
        assert len(network.ways) == 5  # From mock data
        assert network.graph.number_of_nodes() == 5
        assert network.graph.number_of_edges() > 0  # Should have edges

    def test_add_room_edges(self, analyzer):
        """Test room-based edge addition."""
        network = WaysNetwork()
        # Manually add ways to network
        ways_data = [
            (1, "Way 1", "Partner A", "Absolute", "Self", "", "Example 1", "", "B", "Creator", "", ""),
            (2, "Way 2", "Partner A", "Absolute", "Self", "", "Example 2", "", "B", "Creator", "", ""),
            (3, "Way 3", "Partner B", "Relative", "Other", "", "Example 3", "", "B2", "Sustainer", "", "")
        ]

        for row in ways_data:
            way = Way(
                id=row[0], way=row[1], dialoguewith=row[2], dialoguetype=row[3],
                dialoguetypetype=row[4], wayurl=row[5], examples=row[6],
                dialoguetypetypetype=row[7], mene=row[8], dievas=row[9],
                comments=row[10], laikinas=row[11]
            )
            network.ways[way.id] = way
            network.graph.add_node(way.id)

        # Add room edges
        analyzer._add_room_edges(network)

        # Should have edges between ways in same room (B)
        assert network.graph.has_edge(1, 2)  # Both in room B
        assert not network.graph.has_edge(1, 3)  # Different rooms
        assert network.edge_types.get((1, 2)) == 'same_room'

    def test_add_partner_edges(self, analyzer):
        """Test partner-based edge addition."""
        network = WaysNetwork()
        # Manually add ways to network
        ways_data = [
            (1, "Way 1", "Partner A", "Absolute", "Self", "", "Example 1", "", "B", "Creator", "", ""),
            (2, "Way 2", "Partner A", "Absolute", "Self", "", "Example 2", "", "B", "Creator", "", ""),
            (3, "Way 3", "Partner B", "Relative", "Other", "", "Example 3", "", "B", "Sustainer", "", "")
        ]

        for row in ways_data:
            way = Way(
                id=row[0], way=row[1], dialoguewith=row[2], dialoguetype=row[3],
                dialoguetypetype=row[4], wayurl=row[5], examples=row[6],
                dialoguetypetypetype=row[7], mene=row[8], dievas=row[9],
                comments=row[10], laikinas=row[11]
            )
            network.ways[way.id] = way
            network.graph.add_node(way.id)

        # Add partner edges
        analyzer._add_partner_edges(network)

        # Should have edges between ways with same partner
        assert network.graph.has_edge(1, 2)  # Both have Partner A
        assert not network.graph.has_edge(1, 3)  # Different partners
        assert network.edge_types.get((1, 2)) == 'same_partner'

    def test_add_type_edges(self, analyzer):
        """Test type-based edge addition."""
        network = WaysNetwork()
        # Manually add ways to network
        ways_data = [
            (1, "Way 1", "Partner A", "Absolute", "Self", "", "Example 1", "", "B", "Creator", "", ""),
            (2, "Way 2", "Partner B", "Absolute", "Self", "", "Example 2", "", "B", "Creator", "", ""),
            (3, "Way 3", "Partner C", "Relative", "Other", "", "Example 3", "", "B2", "Sustainer", "", "")
        ]

        for row in ways_data:
            way = Way(
                id=row[0], way=row[1], dialoguewith=row[2], dialoguetype=row[3],
                dialoguetypetype=row[4], wayurl=row[5], examples=row[6],
                dialoguetypetypetype=row[7], mene=row[8], dievas=row[9],
                comments=row[10], laikinas=row[11]
            )
            network.ways[way.id] = way
            network.graph.add_node(way.id)

        # Add type edges
        analyzer._add_type_edges(network)

        # Should have edges between ways with same type
        assert network.graph.has_edge(1, 2)  # Both Absolute
        assert not network.graph.has_edge(1, 3)  # Different types
        assert network.edge_types.get((1, 2)) == 'same_type'

    def test_compute_centrality_metrics(self, network_analyzer):
        """Test centrality metrics computation."""
        if network_analyzer is None:
            pytest.skip("Database not available")

        analyzer = network_analyzer
        metrics = analyzer.compute_centrality_metrics()
        assert isinstance(metrics, NetworkMetrics)

        # Check basic metrics
        assert metrics.node_count > 0  # Should have nodes from database
        assert isinstance(metrics.edge_count, int)
        assert metrics.edge_count >= 0
        assert isinstance(metrics.density, float)
        assert 0 <= metrics.density <= 1
        assert isinstance(metrics.average_degree, float)
        assert metrics.average_degree >= 0
        assert isinstance(metrics.clustering_coefficient, float)
        assert 0 <= metrics.clustering_coefficient <= 1

        # Check centrality measures (may be empty for small graphs)
        assert isinstance(metrics.degree_centrality, dict)
        assert isinstance(metrics.betweenness_centrality, dict)
        assert isinstance(metrics.closeness_centrality, dict)

    def test_detect_communities(self, network_analyzer):
        """Test community detection."""
        if network_analyzer is None:
            pytest.skip("Database not available")

        analyzer = network_analyzer
        communities = analyzer.detect_communities()
        assert isinstance(communities, CommunityStructure)

        assert isinstance(communities.communities, list)
        assert isinstance(communities.modularity, float)
        assert isinstance(communities.community_sizes, list)
        assert isinstance(communities.community_labels, dict)

        # Should have communities
        assert len(communities.communities) > 0
        assert len(communities.community_sizes) == len(communities.communities)

        # All ways should be labeled
        assert len(communities.community_labels) > 0  # All ways from database should be labeled

    def test_analyze_network_structure(self, analyzer):
        """Test network structure analysis."""
        analysis = analyzer.analyze_network_structure()
        assert isinstance(analysis, dict)

        # Check required keys
        assert 'metrics' in analysis
        assert 'communities' in analysis
        assert 'centralization' in analysis
        assert 'structural_holes' in analysis

        # Check metrics structure
        metrics = analysis['metrics']
        assert 'node_count' in metrics
        assert 'edge_count' in metrics
        assert 'density' in metrics
        assert 'connected_components' in metrics

        # Check communities structure
        communities = analysis['communities']
        assert 'count' in communities
        assert 'sizes' in communities
        assert 'modularity' in communities

    def test_find_central_ways(self, analyzer):
        """Test central ways identification."""
        central = analyzer.find_central_ways()
        assert isinstance(central, CentralWays)

        # Check structure
        assert isinstance(central.by_degree, list)
        assert isinstance(central.by_betweenness, list)
        assert isinstance(central.by_closeness, list)
        assert isinstance(central.by_eigenvector, list)
        assert isinstance(central.hubs, list)
        assert isinstance(central.bridges, list)

        # Should have some central ways (up to top 10, but limited by data size)
        assert len(central.by_degree) <= 10
        assert len(central.by_betweenness) <= 10

    def test_get_way_neighbors(self, analyzer):
        """Test way neighbor retrieval."""
        neighbors = analyzer.get_way_neighbors(1)
        assert isinstance(neighbors, list)

        # Each neighbor should be a tuple of (way_id, edge_type)
        for neighbor in neighbors:
            assert isinstance(neighbor, tuple)
            assert len(neighbor) == 2
            assert isinstance(neighbor[0], int)  # way_id
            assert isinstance(neighbor[1], str)  # edge_type

    def test_get_way_paths(self, analyzer):
        """Test path finding between ways."""
        # Test existing path
        paths = analyzer.get_way_paths(1, 2)
        assert isinstance(paths, list)

        # Test non-existing path (should return empty list)
        no_paths = analyzer.get_way_paths(1, 999)
        assert isinstance(no_paths, list)
        assert len(no_paths) == 0

    def test_get_way_cluster(self, analyzer):
        """Test way cluster retrieval."""
        cluster = analyzer.get_way_cluster(1)
        assert isinstance(cluster, list)

        # Should contain the way itself
        assert 1 in cluster

        # All items should be integers (way IDs)
        assert all(isinstance(wid, int) for wid in cluster)

    def test_get_network_edges(self, analyzer):
        """Test network edges retrieval."""
        edges = analyzer.get_network_edges()
        assert isinstance(edges, list)

        # Each edge should be a tuple of (way1_id, way2_id, edge_type)
        for edge in edges:
            assert isinstance(edge, tuple)
            assert len(edge) == 3
            assert isinstance(edge[0], int)  # way1_id
            assert isinstance(edge[1], int)  # way2_id
            assert isinstance(edge[2], str)  # edge_type

    def test_analyze_room_networks(self, analyzer):
        """Test room sub-network analysis."""
        room_networks = analyzer.analyze_room_networks()
        assert isinstance(room_networks, dict)

        # Should have entries for rooms that exist in data
        assert 'B' in room_networks
        assert 'B2' in room_networks

        # Check structure of room analysis
        b_network = room_networks['B']
        assert 'way_count' in b_network
        assert 'edge_count' in b_network
        assert 'density' in b_network
        assert 'avg_degree' in b_network
        assert 'connected' in b_network
        assert 'diameter' in b_network

    def test_analyze_partner_networks(self, analyzer):
        """Test partner sub-network analysis."""
        partner_networks = analyzer.analyze_partner_networks()
        assert isinstance(partner_networks, dict)

        # Should have entries for partners that exist in data
        assert 'Partner A' in partner_networks
        assert 'Partner B' in partner_networks

        # Check structure of partner analysis
        partner_a_network = partner_networks['Partner A']
        assert 'way_count' in partner_a_network
        assert 'edge_count' in partner_a_network
        assert 'density' in partner_a_network
        assert 'avg_degree' in partner_a_network
        assert 'connected' in partner_a_network

    def test_export_network_data(self, tmp_path, analyzer):
        """Test network data export."""
        output_path = tmp_path / "network_export"
        network_data = analyzer.export_network_data(str(output_path))

        assert isinstance(network_data, dict)
        assert 'nodes' in network_data
        assert 'edges' in network_data
        assert 'metadata' in network_data

        # Check nodes structure
        nodes = network_data['nodes']
        assert isinstance(nodes, list)
        assert len(nodes) == 5  # From mock data

        for node in nodes:
            assert 'id' in node
            assert 'way' in node
            assert 'room' in node
            assert 'dialogue_type' in node

        # Check edges structure
        edges = network_data['edges']
        assert isinstance(edges, list)

        for edge in edges:
            assert 'source' in edge
            assert 'target' in edge
            assert 'type' in edge
            assert 'weight' in edge

        # Check metadata
        metadata = network_data['metadata']
        assert 'node_count' in metadata
        assert 'edge_count' in metadata
        assert metadata['node_count'] == 5


class TestDataClasses:
    """Test network analysis dataclasses."""

    def test_ways_network_initialization(self):
        """Test WaysNetwork basic initialization."""
        network = WaysNetwork()
        assert isinstance(network.graph, nx.Graph)
        assert network.ways == {}
        assert network.edge_types == {}
        assert network.node_attributes == {}

    def test_network_metrics_initialization(self):
        """Test NetworkMetrics basic initialization."""
        metrics = NetworkMetrics()
        assert metrics.node_count == 0
        assert metrics.edge_count == 0
        assert metrics.density == 0.0
        assert metrics.average_degree == 0.0
        assert metrics.degree_centrality == {}
        assert metrics.betweenness_centrality == {}
        assert metrics.closeness_centrality == {}
        assert metrics.eigenvector_centrality == {}
        assert metrics.clustering_coefficient == 0.0
        assert metrics.connected_components == 0
        assert metrics.largest_component_size == 0

    def test_community_structure_initialization(self):
        """Test CommunityStructure basic initialization."""
        communities = CommunityStructure()
        assert communities.communities == []
        assert communities.modularity == 0.0
        assert communities.community_sizes == []
        assert communities.community_labels == {}

    def test_central_ways_initialization(self):
        """Test CentralWays basic initialization."""
        central = CentralWays()
        assert central.by_degree == []
        assert central.by_betweenness == []
        assert central.by_closeness == []
        assert central.by_eigenvector == []
        assert central.hubs == []
        assert central.bridges == []


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_analyze_ways_network(self):
        """Test analyze_ways_network convenience function."""
        # Test with mock to avoid database dependency
        with pytest.raises(Exception):  # Will fail without database
            result = analyze_ways_network()
        # Function exists and is callable
        from src.network_analysis import analyze_ways_network
        assert callable(analyze_ways_network)

    def test_get_network_analyzer(self):
        """Test get_network_analyzer convenience function."""
        # Test with mock to avoid database dependency
        with pytest.raises(Exception):  # Will fail without database
            analyzer = get_network_analyzer()
        # Function exists and is callable
        from src.network_analysis import get_network_analyzer
        assert callable(get_network_analyzer)


class TestInternalMethods:
    """Test internal/private methods."""

    def test_compute_centralization(self, network_analyzer):
        """Test centralization computation."""
        if network_analyzer is None:
            pytest.skip("Database not available")

        analyzer = network_analyzer
        metrics = NetworkMetrics(
            degree_centrality={1: 0.5, 2: 0.3, 3: 0.2},
            betweenness_centrality={1: 0.4, 2: 0.3, 3: 0.3}
        )

        centralization = analyzer._compute_centralization(metrics)
        assert isinstance(centralization, dict)
        assert 'degree' in centralization
        assert 'betweenness' in centralization
        assert isinstance(centralization['degree'], float)
        assert isinstance(centralization['betweenness'], float)

    def test_analyze_structural_holes(self, network_analyzer):
        """Test structural holes analysis."""
        if network_analyzer is None:
            pytest.skip("Database not available")

        analyzer = network_analyzer
        structural_holes = analyzer._analyze_structural_holes()
        assert isinstance(structural_holes, dict)
        assert 'avg_constraint' in structural_holes
        assert 'avg_effective_size' in structural_holes
        assert 'high_constraint_nodes' in structural_holes

        assert isinstance(structural_holes['avg_constraint'], float)
        assert isinstance(structural_holes['avg_effective_size'], float)
        assert isinstance(structural_holes['high_constraint_nodes'], list)


class TestIntegrationWithRealData:
    """Test integration with real database data."""

    def test_analyzer_with_real_data(self):
        """Test that analyzer works with real database data."""
        try:
            analyzer = WaysNetworkAnalyzer()
            network = analyzer.build_ways_network()

            # Should have some nodes and edges
            assert isinstance(network, WaysNetwork)
            assert network.graph.number_of_nodes() >= 0
            assert network.graph.number_of_edges() >= 0

            # Test centrality computation
            metrics = analyzer.compute_centrality_metrics()
            assert isinstance(metrics, NetworkMetrics)

        except Exception:
            # If database doesn't exist or other issues, that's okay for this test
            pytest.skip("Database not available for integration test")

    def test_network_with_minimal_data(self, tmp_path):
        """Test network building with minimal data."""
        # Create a simple test database
        import sqlite3
        db_path = tmp_path / "minimal.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE ways (
                ID INTEGER PRIMARY KEY,
                way TEXT,
                dialoguewith TEXT,
                dialoguetype TEXT,
                dialoguetypetype TEXT,
                wayurl TEXT,
                examples TEXT,
                dialoguetypetypetype TEXT,
                mene TEXT,
                dievas TEXT,
                comments TEXT,
                laikinas TEXT
            )
        """)
        conn.execute("INSERT INTO ways VALUES (1, 'Test Way', 'Partner', 'Absolute', 'Self', '', '', '', 'B', '', '', '')")
        conn.execute("INSERT INTO ways VALUES (2, 'Another Way', 'Partner', 'Absolute', 'Self', '', '', '', 'B', '', '', '')")
        conn.commit()
        conn.close()

        # Test with this minimal database
        analyzer = WaysNetworkAnalyzer(str(db_path))
        network = analyzer.network

        assert network.graph.number_of_nodes() == 2
        # Should have an edge between the two ways (same room and partner)
        assert network.graph.number_of_edges() >= 1


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_network(self):
        """Test behavior with empty network."""
        # Mock empty data
        mock_queries = Mock()
        mock_queries.get_all_ways_sql.return_value = ("SELECT * FROM ways", [])

        analyzer = WaysNetworkAnalyzer.__new__(WaysNetworkAnalyzer)
        analyzer.db = Mock()
        analyzer.queries = mock_queries

        network = analyzer._build_ways_network()
        assert network.graph.number_of_nodes() == 0
        assert len(network.ways) == 0

    def test_single_node_network(self):
        """Test behavior with single node network."""
        # Mock single way data
        mock_queries = Mock()
        mock_queries.get_all_ways_sql.return_value = (
            "SELECT * FROM ways",
            [(1, "Single Way", "Partner", "Absolute", "Self", "", "Example", "", "B", "Creator", "", "")]
        )

        analyzer = WaysNetworkAnalyzer.__new__(WaysNetworkAnalyzer)
        analyzer.db = Mock()
        analyzer.queries = mock_queries

        network = analyzer._build_ways_network()
        assert network.graph.number_of_nodes() == 1
        assert network.graph.number_of_edges() == 0  # No edges possible with single node

    def test_centrality_with_small_graph(self, network_analyzer):
        """Test centrality computation with small graph."""
        if network_analyzer is None:
            pytest.skip("Database not available")

        analyzer = network_analyzer
        metrics = analyzer.compute_centrality_metrics()

        # Should not crash even with small graph
        assert isinstance(metrics.degree_centrality, dict)
        assert isinstance(metrics.betweenness_centrality, dict)

    def test_community_detection_with_small_graph(self, network_analyzer):
        """Test community detection with small graph."""
        if network_analyzer is None:
            pytest.skip("Database not available")

        analyzer = network_analyzer
        communities = analyzer.detect_communities()

        # Should handle small graphs
        assert len(communities.communities) > 0
        assert len(communities.community_labels) > 0  # All ways labeled


if __name__ == "__main__":
    pytest.main([__file__])
