"""Tests for ways-specific statistical functions with real data only."""

import pytest
from src.ways_statistics import analyze_way_distributions, compute_way_correlations, analyze_type_room_independence, compute_way_diversity_metrics
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
            assert 'std' in dist
            assert 'min' in dist
            assert 'max' in dist
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
        assert 'types' in result
        assert 'rooms' in result

        assert result['chi_square_statistic'] >= 0.0
        assert result['degrees_of_freedom'] >= 0
        assert 0.0 <= result['p_value'] <= 1.0
        assert isinstance(result['significant'], bool)
        assert isinstance(result['contingency_table'], list)
        assert len(result['types']) > 0
        assert len(result['rooms']) > 0

    def test_compute_way_diversity_metrics(self, db):
        """Test diversity metrics computation."""
        result = compute_way_diversity_metrics(db)

        assert isinstance(result, dict)
        assert 'room_diversity' in result
        assert 'type_diversity' in result
        assert 'partner_diversity' in result
        assert 'overall' in result

        # Check diversity metrics
        for diversity_name in ['room_diversity', 'type_diversity', 'partner_diversity']:
            diversity = result[diversity_name]
            assert 'shannon_index' in diversity
            assert 'simpson_index' in diversity
            assert 'num_categories' in diversity
            assert 'evenness' in diversity


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
        assert 'occupied_rooms' in overall
        assert 'total_rooms' in overall
        assert 'room_coverage_ratio' in overall

        assert overall['total_ways'] > 0
        assert overall['occupied_rooms'] > 0
        assert overall['total_rooms'] > 0
        assert 0.0 <= overall['room_coverage_ratio'] <= 1.0

    def test_compute_framework_completeness(self, db):
        """Test framework completeness computation."""
        result = compute_framework_completeness(db)

        assert isinstance(result, dict)
        assert 'believing' in result
        assert 'caring' in result
        assert 'relative_learning' in result

        # Check structure of each framework
        for framework_name in ['believing', 'caring', 'relative_learning']:
            framework = result[framework_name]
            assert 'total_ways' in framework
            assert 'room_coverage' in framework
            assert 'balance_score' in framework
            assert 'completeness_score' in framework

    def test_compute_way_interconnectedness(self, db):
        """Test way interconnectedness computation."""
        result = compute_way_interconnectedness(db)

        assert isinstance(result, dict)
        assert 'network_structure' in result
        assert 'centrality_measures' in result
        assert 'community_structure' in result
        assert 'interconnectedness_score' in result

        # Check network structure
        network = result['network_structure']
        assert 'nodes' in network
        assert 'edges' in network
        assert 'density' in network
        assert 'avg_degree' in network

        assert network['nodes'] > 0
        assert network['edges'] >= 0
        assert 0.0 <= network['density'] <= 1.0
        assert network['avg_degree'] >= 0.0

        # Check interconnectedness score
        assert 0.0 <= result['interconnectedness_score'] <= 1.0

    def test_compute_room_balance_metrics(self, db):
        """Test room balance metrics computation."""
        result = compute_room_balance_metrics(db)

        assert isinstance(result, dict)
        assert 'room_distribution' in result
        assert 'balance_analysis' in result

        room_dist = result['room_distribution']
        assert isinstance(room_dist, dict)

        balance = result['balance_analysis']
        assert 'mean_ways_per_room' in balance
        assert 'variance' in balance
        assert 'std_deviation' in balance
        assert 'coefficient_of_variation' in balance
        assert 'balance_score' in balance
        assert 'assessment' in balance

        assert balance['mean_ways_per_room'] > 0
        assert balance['variance'] >= 0
        assert balance['std_deviation'] >= 0
        assert 0.0 <= balance['coefficient_of_variation'] <= 2.0
        assert 0.0 <= balance['balance_score'] <= 1.0
        assert balance['assessment'] in ['balanced', 'unbalanced', 'single_room']


if __name__ == "__main__":
    pytest.main([__file__])
