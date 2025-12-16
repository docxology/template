"""Comprehensive tests for compatibility_prediction module."""
import pytest
import numpy as np
from compatibility_prediction import (
    predict_compatibility_from_phylogeny,
    predict_compatibility_from_cambium,
    predict_compatibility_from_growth_rate,
    predict_compatibility_combined,
    predict_success_probability
)


class TestPhylogenyPrediction:
    """Test phylogenetic compatibility prediction."""
    
    def test_same_species(self):
        """Test same species (distance = 0)."""
        compat = predict_compatibility_from_phylogeny(0.0)
        assert compat == pytest.approx(1.0)
    
    def test_distant_species(self):
        """Test distant species."""
        compat = predict_compatibility_from_phylogeny(1.0)
        assert compat < 0.5


class TestCambiumPrediction:
    """Test cambium-based prediction."""
    
    def test_perfect_match(self):
        """Test perfect cambium match."""
        compat = predict_compatibility_from_cambium(1.0, 1.0)
        assert compat == pytest.approx(1.0)
    
    def test_mismatch(self):
        """Test cambium mismatch."""
        compat = predict_compatibility_from_cambium(1.0, 2.0, tolerance=0.2)
        assert compat < 1.0
    
    def test_cambium_zero_thickness(self):
        """Test cambium prediction with zero thickness."""
        compat = predict_compatibility_from_cambium(0.0, 1.0)
        assert compat == 0.0
    
    def test_cambium_zero_scion_thickness(self):
        """Test cambium prediction with zero scion thickness."""
        compat = predict_compatibility_from_cambium(1.0, 0.0)
        assert compat == 0.0
    
    def test_cambium_both_zero(self):
        """Test cambium prediction with both zero."""
        compat = predict_compatibility_from_cambium(0.0, 0.0)
        assert compat == 0.0


class TestCombinedPrediction:
    """Test combined compatibility prediction."""
    
    def test_combined_prediction(self):
        """Test combined prediction."""
        compat = predict_compatibility_combined(
            phylogenetic_distance=0.2,
            cambium_match=0.9,
            growth_rate_match=0.8
        )
        assert 0.0 <= compat <= 1.0
    
    def test_combined_prediction_custom_weights(self):
        """Test combined prediction with custom weights."""
        custom_weights = {
            "phylogeny": 0.6,
            "cambium": 0.3,
            "growth_rate": 0.1
        }
        compat = predict_compatibility_combined(
            phylogenetic_distance=0.2,
            cambium_match=0.9,
            growth_rate_match=0.8,
            weights=custom_weights
        )
        assert 0.0 <= compat <= 1.0


class TestGrowthRatePrediction:
    """Test growth rate-based prediction."""
    
    def test_growth_rate_zero_rootstock(self):
        """Test growth rate prediction with zero rootstock rate."""
        compat = predict_compatibility_from_growth_rate(0.0, 1.0)
        assert compat == 0.0
    
    def test_growth_rate_zero_scion(self):
        """Test growth rate prediction with zero scion rate."""
        compat = predict_compatibility_from_growth_rate(1.0, 0.0)
        assert compat == 0.0
    
    def test_growth_rate_both_zero(self):
        """Test growth rate prediction with both zero."""
        compat = predict_compatibility_from_growth_rate(0.0, 0.0)
        assert compat == 0.0


class TestSuccessProbability:
    """Test success probability prediction."""
    
    def test_high_probability(self):
        """Test high success probability."""
        prob = predict_success_probability(0.9, 0.9, 0.9, 0.9)
        assert prob > 0.8
    
    def test_low_probability(self):
        """Test low success probability."""
        prob = predict_success_probability(0.3, 0.3, 0.3, 0.3)
        assert prob < 0.5


if __name__ == "__main__":
    pytest.main([__file__])

