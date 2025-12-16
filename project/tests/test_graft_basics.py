"""Comprehensive tests for graft_basics module to ensure 100% coverage."""
import pytest
import numpy as np
from graft_basics import (
    check_cambium_alignment,
    calculate_graft_angle,
    estimate_callus_formation_time,
    calculate_union_strength,
    check_seasonal_timing,
    calculate_scion_length,
    estimate_success_probability
)


class TestCambiumAlignment:
    """Test cambium alignment checks."""
    
    def test_perfect_match(self):
        """Test perfect diameter match."""
        is_compat, ratio = check_cambium_alignment(15.0, 15.0)
        assert is_compat is True
        assert ratio == pytest.approx(1.0)
    
    def test_within_tolerance(self):
        """Test diameters within tolerance."""
        is_compat, ratio = check_cambium_alignment(15.0, 14.5, tolerance=0.1)
        assert is_compat is True
    
    def test_outside_tolerance(self):
        """Test diameters outside tolerance."""
        is_compat, ratio = check_cambium_alignment(15.0, 20.0, tolerance=0.1)
        assert is_compat is False
    
    def test_invalid_diameters(self):
        """Test with invalid diameters."""
        is_compat, ratio = check_cambium_alignment(0.0, 15.0)
        assert is_compat is False
        assert ratio == 0.0


class TestGraftAngle:
    """Test graft angle calculations."""
    
    def test_whip_technique(self):
        """Test whip grafting angle."""
        angle = calculate_graft_angle(15.0, 15.0, "whip")
        assert angle == 35.0
    
    def test_cleft_technique(self):
        """Test cleft grafting angle."""
        angle = calculate_graft_angle(15.0, 15.0, "cleft")
        assert angle == 40.0
    
    def test_bark_technique(self):
        """Test bark grafting angle."""
        angle = calculate_graft_angle(15.0, 15.0, "bark")
        assert angle == 25.0
    
    def test_approach_technique(self):
        """Test approach grafting angle."""
        angle = calculate_graft_angle(15.0, 15.0, "approach")
        assert angle == 35.0
    
    def test_default_angle(self):
        """Test default angle for unknown technique."""
        angle = calculate_graft_angle(15.0, 15.0, "unknown")
        assert angle == 30.0


class TestCallusFormation:
    """Test callus formation time estimation."""
    
    def test_optimal_conditions(self):
        """Test with optimal conditions."""
        time = estimate_callus_formation_time(22.0, 0.8, 0.9)
        assert 7.0 <= time <= 14.0
    
    def test_cold_temperature(self):
        """Test with cold temperature."""
        time = estimate_callus_formation_time(10.0, 0.8, 0.9)
        assert time > 14.0
    
    def test_low_humidity(self):
        """Test with low humidity."""
        time = estimate_callus_formation_time(22.0, 0.4, 0.9)
        assert time > 10.0
    
    def test_low_compatibility(self):
        """Test with low compatibility."""
        time = estimate_callus_formation_time(22.0, 0.8, 0.3)
        assert time > 15.0
    
    def test_humidity_percentage(self):
        """Test humidity given as percentage (> 1.0)."""
        time = estimate_callus_formation_time(22.0, 80.0, 0.8)  # 80% humidity
        assert time > 0
    
    def test_hot_temperature(self):
        """Test callus formation with hot temperature (> 30°C)."""
        time = estimate_callus_formation_time(35.0, 0.8, 0.8)
        assert time > 10.0  # Should be slower


class TestUnionStrength:
    """Test union strength calculations."""
    
    def test_initial_strength(self):
        """Test initial union strength."""
        # At day 0, there is some initial mechanical connection
        # Initial strength = compatibility * technique_quality = 0.8 * 0.8 = 0.64
        strength = calculate_union_strength(0.0, 0.8, 0.8)
        assert 0.6 <= strength <= 0.7  # Initial mechanical connection present
    
    def test_increasing_strength(self):
        """Test increasing strength over time."""
        strength_10 = calculate_union_strength(10.0, 0.8, 0.8)
        strength_30 = calculate_union_strength(30.0, 0.8, 0.8)
        assert strength_30 > strength_10
    
    def test_high_compatibility(self):
        """Test with high compatibility."""
        strength = calculate_union_strength(30.0, 0.95, 0.9)
        assert strength > 0.7
    
    def test_low_compatibility(self):
        """Test with low compatibility."""
        strength = calculate_union_strength(30.0, 0.3, 0.9)
        assert strength < 0.5


class TestSeasonalTiming:
    """Test seasonal timing checks."""
    
    def test_optimal_temperate_season(self):
        """Test optimal temperate season."""
        is_suitable, reason = check_seasonal_timing(3, "temperate", "northern")
        assert is_suitable is True
        assert "optimal" in reason.lower() or "acceptable" in reason.lower()
    
    def test_winter_temperate(self):
        """Test winter for temperate species."""
        is_suitable, reason = check_seasonal_timing(12, "temperate", "northern")
        assert is_suitable is False
    
    def test_tropical_season(self):
        """Test tropical species timing."""
        is_suitable, reason = check_seasonal_timing(7, "tropical", "northern")
        assert is_suitable is True
    
    def test_southern_hemisphere(self):
        """Test southern hemisphere adjustment."""
        is_suitable, reason = check_seasonal_timing(8, "temperate", "southern")
        assert is_suitable is True  # Should be spring in southern hemisphere
    
    def test_temperate_too_early(self):
        """Test temperate species too early (Nov-Dec)."""
        is_suitable, reason = check_seasonal_timing(11, "temperate", "northern")
        assert is_suitable is False
        assert "early" in reason.lower() or "dormancy" in reason.lower()
    
    def test_temperate_too_late(self):
        """Test temperate species too late (outside optimal months)."""
        is_suitable, reason = check_seasonal_timing(7, "temperate", "northern")
        assert is_suitable is False
        assert "late" in reason.lower() or "growth" in reason.lower()
    
    def test_tropical_optimal(self):
        """Test tropical species optimal season."""
        is_suitable, reason = check_seasonal_timing(7, "tropical", "northern")
        assert is_suitable is True
        assert "optimal" in reason.lower() or "acceptable" in reason.lower()
    
    def test_tropical_acceptable(self):
        """Test tropical species acceptable season (non-optimal months)."""
        is_suitable, reason = check_seasonal_timing(1, "tropical", "northern")
        assert is_suitable is True
        assert "acceptable" in reason.lower()
    
    def test_subtropical_optimal(self):
        """Test subtropical species optimal season."""
        is_suitable, reason = check_seasonal_timing(12, "subtropical", "northern")
        assert is_suitable is True
        assert "optimal" in reason.lower()
    
    def test_subtropical_acceptable(self):
        """Test subtropical species acceptable season."""
        is_suitable, reason = check_seasonal_timing(10, "subtropical", "northern")
        assert is_suitable is True
        assert "acceptable" in reason.lower()
    
    def test_subtropical_outside(self):
        """Test subtropical species outside optimal season."""
        is_suitable, reason = check_seasonal_timing(6, "subtropical", "northern")
        assert is_suitable is False
        assert "outside" in reason.lower()
    
    def test_unknown_species_type(self):
        """Test unknown species type."""
        is_suitable, reason = check_seasonal_timing(5, "unknown", "northern")
        assert is_suitable is True  # Should default to acceptable
        assert "unknown" in reason.lower() or "acceptable" in reason.lower()


class TestScionLength:
    """Test scion length calculations."""
    
    def test_basic_calculation(self):
        """Test basic scion length."""
        length = calculate_scion_length(15.0, "whip", 3)
        assert 10.0 <= length <= 20.0
    
    def test_bud_grafting(self):
        """Test bud grafting length."""
        length = calculate_scion_length(15.0, "bud", 1)
        assert length == pytest.approx(1.0, abs=2.0)
    
    def test_large_rootstock(self):
        """Test with large rootstock."""
        length = calculate_scion_length(30.0, "whip", 3)
        assert length >= 10.0
    
    def test_cleft_technique_length(self):
        """Test cleft technique scion length."""
        length = calculate_scion_length(15.0, "cleft", 3)
        assert length > 0
    
    def test_bark_technique_length(self):
        """Test bark technique scion length."""
        length = calculate_scion_length(15.0, "bark", 3)
        assert length > 0
    
    def test_unknown_technique_length(self):
        """Test unknown technique uses default."""
        length = calculate_scion_length(15.0, "unknown_technique", 3)
        assert length > 0


class TestSuccessProbability:
    """Test success probability estimation."""
    
    def test_high_probability(self):
        """Test with all high factors."""
        prob = estimate_success_probability(0.9, 0.9, 0.9, 0.9)
        assert prob > 0.8
    
    def test_low_probability(self):
        """Test with all low factors."""
        prob = estimate_success_probability(0.3, 0.3, 0.3, 0.3)
        assert prob < 0.5
    
    def test_weighted_combination(self):
        """Test weighted combination."""
        prob = estimate_success_probability(1.0, 0.0, 0.0, 0.0)
        assert prob == pytest.approx(0.4)  # Compatibility weight


if __name__ == "__main__":
    pytest.main([__file__])

