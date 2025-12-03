"""Tests for ways-specific statistical functions."""

import pytest
from src.statistics import analyze_way_distributions, compute_way_correlations, analyze_type_room_independence, compute_way_diversity_metrics
from src.metrics import compute_way_coverage_metrics, compute_framework_completeness, compute_way_interconnectedness, compute_room_balance_metrics
from src.database import WaysDatabase


class TestWaysStatistics:
    """Test ways-specific statistical functions."""

    @pytest.fixture
    def db(self):
        """Get database instance."""
        return WaysDatabase()

    def test_analyze_way_distributions(self, db):
        """Test way distribution analysis."""
        result = analyze_way_distributions(db)

        assert isinstance(result, dict)
        assert 'room_distribution' in result
        assert 'type_distribution' in result
        assert 'partner_distribution' in result

        # Check that distributions have expected structure
        for dist_name in ['room_distribution', 'type_distribution', 'partner_distribution']:
            dist = result[dist_name]
            assert 'counts' in dist
            assert 'mean' in dist
            assert isinstance(dist['counts'], list)
            assert all(isinstance(c, int) for c in dist['counts'])

    def test_compute_way_correlations(self, db):
        """Test correlation computation."""
        result = compute_way_correlations(db)

        assert isinstance(result, dict)
        assert 'correlations' in result
        assert 'mappings' in result
        assert 'sample_size' in result

        assert isinstance(result['correlations'], dict)
        assert result['sample_size'] > 0

    def test_test_type_room_independence(self, db):
        """Test chi-square independence test."""
        result = analyze_type_room_independence(db)

        assert isinstance(result, dict)
        assert 'chi_square_statistic' in result
        assert 'degrees_of_freedom' in result
        assert 'p_value' in result
        assert 'significant' in result
        assert 'contingency_table' in result

        assert isinstance(result['chi_square_statistic'], float)
        assert isinstance(result['significant'], bool)

    def test_compute_way_diversity_metrics(self, db):
        """Test diversity metrics computation."""
        result = compute_way_diversity_metrics(db)

        assert isinstance(result, dict)
        assert 'room_diversity' in result
        assert 'type_diversity' in result
        assert 'partner_diversity' in result
        assert 'overall' in result

        # Check diversity indices
        for diversity_type in ['room_diversity', 'type_diversity', 'partner_diversity']:
            diversity = result[diversity_type]
            assert 'shannon_index' in diversity
            assert 'simpson_index' in diversity
            assert 'evenness' in diversity
            assert isinstance(diversity['shannon_index'], float)


class TestWaysMetrics:
    """Test ways-specific metrics functions."""

    @pytest.fixture
    def db(self):
        """Get database instance."""
        return WaysDatabase()

    def test_compute_way_coverage_metrics(self, db):
        """Test coverage metrics computation."""
        result = compute_way_coverage_metrics(db)

        assert isinstance(result, dict)
        assert 'overall_coverage' in result
        assert 'room_coverage' in result

        overall = result['overall_coverage']
        assert 'total_ways' in overall
        assert 'room_coverage_ratio' in overall
        assert isinstance(overall['room_coverage_ratio'], float)
        assert 0 <= overall['room_coverage_ratio'] <= 1

    def test_compute_framework_completeness(self, db):
        """Test framework completeness computation."""
        result = compute_framework_completeness(db)

        assert isinstance(result, dict)
        assert 'overall' in result

        # Should have framework-specific results
        framework_keys = [k for k in result.keys() if k != 'overall']
        assert len(framework_keys) > 0

        for framework in framework_keys:
            assert 'completeness_score' in result[framework]
            assert isinstance(result[framework]['completeness_score'], float)

    def test_compute_way_interconnectedness(self, db):
        """Test interconnectedness computation."""
        result = compute_way_interconnectedness(db)

        assert isinstance(result, dict)
        assert 'network_structure' in result
        assert 'community_structure' in result
        assert 'interconnectedness_score' in result

        network = result['network_structure']
        assert 'nodes' in network
        assert 'edges' in network
        assert 'density' in network
        assert isinstance(network['density'], float)

    def test_compute_room_balance_metrics(self, db):
        """Test room balance metrics computation."""
        result = compute_room_balance_metrics(db)

        assert isinstance(result, dict)
        assert 'room_distribution' in result
        assert 'balance_analysis' in result

        balance = result['balance_analysis']
        assert 'balance_score' in balance
        assert 'assessment' in balance
        assert isinstance(balance['balance_score'], float)
        assert balance['assessment'] in ['well_balanced', 'moderately_balanced', 'unbalanced', 'single_room']
