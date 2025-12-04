"""Tests for comprehensive_analysis.py script.

Tests the comprehensive statistical analysis script that generates
JSON/CSV exports for manuscript integration.
"""

import pytest
import json
import csv
from pathlib import Path
import tempfile
import shutil

# Add project src and scripts to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "scripts"))
sys.path.insert(0, str(project_root.parent))

from comprehensive_analysis import ComprehensiveWaysAnalyzer
from database import WaysDatabase
from sql_queries import WaysSQLQueries


class TestComprehensiveWaysAnalyzer:
    """Test suite for ComprehensiveWaysAnalyzer."""

    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = ComprehensiveWaysAnalyzer()
        assert analyzer.analyzer is not None
        assert analyzer.network_analyzer is not None
        assert analyzer.db is not None
        assert analyzer.queries is not None

    def test_calculate_entropy(self):
        """Test entropy calculation."""
        analyzer = ComprehensiveWaysAnalyzer()
        
        # Test uniform distribution
        uniform_dist = {'A': 5, 'B': 5, 'C': 5}
        entropy = analyzer.calculate_entropy(uniform_dist)
        assert entropy > 0
        assert entropy < 2.0  # Should be less than log2(3) ≈ 1.585
        
        # Test single category
        single_dist = {'A': 10}
        entropy = analyzer.calculate_entropy(single_dist)
        assert entropy == 0.0
        
        # Test empty distribution
        empty_dist = {}
        entropy = analyzer.calculate_entropy(empty_dist)
        assert entropy == 0.0

    def test_calculate_mutual_information(self):
        """Test mutual information calculation."""
        analyzer = ComprehensiveWaysAnalyzer()
        
        # Test independent distributions
        independent = {
            'A': {'X': 5, 'Y': 5},
            'B': {'X': 5, 'Y': 5}
        }
        mi = analyzer.calculate_mutual_information(independent)
        assert mi >= 0  # Should be close to 0 for independence
        
        # Test empty
        empty = {}
        mi = analyzer.calculate_mutual_information(empty)
        assert mi == 0.0

    def test_build_network_graph(self):
        """Test network graph construction."""
        analyzer = ComprehensiveWaysAnalyzer()
        network_data = analyzer.build_network_graph()
        
        assert 'nodes' in network_data
        assert 'edges' in network_data
        assert 'metrics' in network_data
        assert 'centrality' in network_data
        assert 'central_ways' in network_data
        
        # Check metrics
        metrics = network_data['metrics']
        assert metrics['node_count'] > 0
        assert metrics['edge_count'] > 0
        assert metrics['average_degree'] > 0
        assert 'clustering_coefficient' in metrics

    def test_analyze_text_content(self):
        """Test text analysis functionality."""
        analyzer = ComprehensiveWaysAnalyzer()
        text_analysis = analyzer.analyze_text_content()
        
        assert 'total_ways' in text_analysis
        assert 'ways_with_examples' in text_analysis
        assert 'avg_way_name_length' in text_analysis
        assert 'keyword_frequency' in text_analysis
        assert text_analysis['total_ways'] > 0

    def test_generate_comprehensive_stats(self):
        """Test comprehensive statistics generation."""
        analyzer = ComprehensiveWaysAnalyzer()
        stats = analyzer.generate_comprehensive_stats()
        
        assert 'basic_stats' in stats
        assert 'distributions' in stats
        assert 'cross_tabulations' in stats
        assert 'information_theory' in stats
        assert 'network_analysis' in stats
        assert 'text_analysis' in stats
        
        # Check basic stats
        basic = stats['basic_stats']
        assert basic['total_ways'] > 0
        assert basic['room_diversity'] > 0
        assert basic['type_diversity'] > 0

    def test_export_to_json(self):
        """Test JSON export functionality."""
        analyzer = ComprehensiveWaysAnalyzer()
        stats = analyzer.generate_comprehensive_stats()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_stats.json"
            analyzer.export_to_json(stats, output_path)
            
            assert output_path.exists()
            
            # Verify JSON is valid
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            assert loaded['basic_stats']['total_ways'] == stats['basic_stats']['total_ways']

    def test_export_to_csv(self):
        """Test CSV export functionality."""
        analyzer = ComprehensiveWaysAnalyzer()
        stats = analyzer.generate_comprehensive_stats()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            analyzer.export_to_csv(stats, output_dir)
            
            # Check CSV files were created
            room_csv = output_dir / "room_distribution.csv"
            type_csv = output_dir / "dialogue_type_distribution.csv"
            crosstab_csv = output_dir / "type_room_crosstab.csv"
            centrality_csv = output_dir / "network_centrality.csv"
            
            assert room_csv.exists()
            assert type_csv.exists()
            assert crosstab_csv.exists()
            assert centrality_csv.exists()
            
            # Verify CSV content
            with open(room_csv, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                assert len(rows) > 1  # Header + data
                assert rows[0] == ['Room', 'Count', 'Percentage']


class TestComprehensiveAnalysisIntegration:
    """Integration tests for comprehensive analysis script."""

    def test_full_analysis_pipeline(self):
        """Test complete analysis pipeline."""
        analyzer = ComprehensiveWaysAnalyzer()
        
        # Generate stats
        stats = analyzer.generate_comprehensive_stats()
        
        # Verify all required sections present
        required_sections = [
            'basic_stats', 'distributions', 'cross_tabulations',
            'information_theory', 'network_analysis', 'text_analysis'
        ]
        for section in required_sections:
            assert section in stats, f"Missing section: {section}"
        
        # Verify data quality
        assert stats['basic_stats']['total_ways'] == 210
        assert stats['network_analysis']['metrics']['node_count'] == 210
        assert stats['network_analysis']['metrics']['edge_count'] > 0

    def test_network_metrics_accuracy(self):
        """Test that network metrics are calculated correctly."""
        analyzer = ComprehensiveWaysAnalyzer()
        network_data = analyzer.build_network_graph()
        
        metrics = network_data['metrics']
        nodes = metrics['node_count']
        edges = metrics['edge_count']
        
        # Average degree should be 2*edges/nodes
        expected_avg_degree = (2 * edges) / nodes if nodes > 0 else 0
        assert abs(metrics['average_degree'] - expected_avg_degree) < 0.1
        
        # Density should be 2*edges/(nodes*(nodes-1))
        if nodes > 1:
            expected_density = (2 * edges) / (nodes * (nodes - 1))
            assert abs(metrics['density'] - expected_density) < 0.001
