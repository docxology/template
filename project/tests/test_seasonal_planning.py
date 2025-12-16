"""Comprehensive tests for seasonal_planning module."""
import pytest
from seasonal_planning import (
    calculate_optimal_grafting_window,
    get_seasonal_suitability,
    calculate_temperature_suitability,
    generate_grafting_calendar,
    adjust_for_climate_zone
)


class TestGraftingWindow:
    """Test grafting window calculations."""
    
    def test_temperate_window(self):
        """Test temperate species window."""
        start, end = calculate_optimal_grafting_window("temperate", "northern")
        assert 1 <= start <= 12
        assert 1 <= end <= 12
    
    def test_tropical_window(self):
        """Test tropical species window."""
        start, end = calculate_optimal_grafting_window("tropical", "northern")
        assert 1 <= start <= 12
        assert 1 <= end <= 12
    
    def test_subtropical_window(self):
        """Test subtropical species window."""
        start, end = calculate_optimal_grafting_window("subtropical", "northern")
        assert 1 <= start <= 12
        assert 1 <= end <= 12
    
    def test_southern_hemisphere_window(self):
        """Test southern hemisphere adjustment."""
        start, end = calculate_optimal_grafting_window("temperate", "southern")
        assert 1 <= start <= 12
        assert 1 <= end <= 12
    
    def test_unknown_species_type_window(self):
        """Test unknown species type returns default window."""
        start, end = calculate_optimal_grafting_window("unknown", "northern")
        assert start == 3  # Default spring
        assert end == 5


class TestSeasonalSuitability:
    """Test seasonal suitability."""
    
    def test_optimal_month(self):
        """Test optimal month."""
        is_suitable, reason = get_seasonal_suitability(3, "temperate", "northern")
        assert is_suitable is True
    
    def test_suboptimal_month(self):
        """Test suboptimal month."""
        is_suitable, reason = get_seasonal_suitability(7, "temperate", "northern")
        assert is_suitable is False


class TestTemperatureSuitability:
    """Test temperature suitability."""
    
    def test_optimal_temperature(self):
        """Test optimal temperature."""
        score = calculate_temperature_suitability(22.0, "temperate")
        assert score == pytest.approx(1.0)
    
    def test_cold_temperature(self):
        """Test cold temperature."""
        score = calculate_temperature_suitability(5.0, "temperate")
        assert score < 1.0
    
    def test_hot_temperature(self):
        """Test hot temperature."""
        score = calculate_temperature_suitability(35.0, "temperate")
        assert score < 1.0
    
    def test_tropical_optimal(self):
        """Test tropical optimal temperature."""
        score = calculate_temperature_suitability(28.0, "tropical")
        assert score > 0.8
    
    def test_unknown_species_type(self):
        """Test unknown species type."""
        score = calculate_temperature_suitability(22.0, "unknown")
        assert 0.0 <= score <= 1.0
    
    def test_temperature_below_optimal(self):
        """Test temperature below optimal range."""
        score = calculate_temperature_suitability(12.0, "temperate")
        # 12 is in acceptable range (10-30) but below optimal (18-25)
        assert 0.0 < score < 1.0
    
    def test_temperature_above_optimal(self):
        """Test temperature above optimal range."""
        score = calculate_temperature_suitability(28.0, "temperate")
        # 28 is in acceptable range (10-30) but above optimal (18-25)
        assert 0.0 < score < 1.0
    
    def test_temperature_outside_acceptable(self):
        """Test temperature outside acceptable range."""
        score = calculate_temperature_suitability(5.0, "temperate")
        assert score == 0.0  # Below acceptable range
    
    def test_temperature_above_acceptable(self):
        """Test temperature above acceptable range."""
        score = calculate_temperature_suitability(35.0, "temperate")
        assert score == 0.0  # Above acceptable range
    
    def test_subtropical_temperature(self):
        """Test subtropical temperature suitability."""
        score = calculate_temperature_suitability(20.0, "subtropical")
        assert 0.0 <= score <= 1.0


class TestGraftingCalendar:
    """Test grafting calendar generation."""
    
    def test_calendar_generation(self):
        """Test calendar generation."""
        calendar = generate_grafting_calendar("temperate", "northern")
        assert len(calendar) == 12
        assert all(1 <= month <= 12 for month in calendar.keys())
    
    def test_calendar_tropical(self):
        """Test tropical calendar."""
        calendar = generate_grafting_calendar("tropical", "northern")
        assert len(calendar) == 12
        # Verify calendar has data for all months
        assert all(isinstance(v, dict) for v in calendar.values())
    
    def test_calendar_subtropical(self):
        """Test subtropical calendar."""
        calendar = generate_grafting_calendar("subtropical", "northern")
        assert len(calendar) == 12
    
    def test_calendar_southern_hemisphere(self):
        """Test calendar generation for southern hemisphere."""
        calendar = generate_grafting_calendar("temperate", "southern")
        assert len(calendar) == 12
        # Should have different months suitable due to hemisphere offset
        assert all(isinstance(v, dict) for v in calendar.values())
        assert all("is_suitable" in v for v in calendar.values())


class TestClimateZone:
    """Test climate zone adjustments."""
    
    def test_adjust_for_climate_zone(self):
        """Test climate zone adjustment."""
        base_window = (2, 4)  # Feb to Apr
        adjusted = adjust_for_climate_zone(base_window, "mediterranean")
        assert isinstance(adjusted, tuple)
        assert len(adjusted) == 2
        assert 1 <= adjusted[0] <= 12
        assert 1 <= adjusted[1] <= 12
    
    def test_adjust_continental(self):
        """Test continental climate adjustment."""
        base_window = (2, 4)
        adjusted = adjust_for_climate_zone(base_window, "continental")
        assert isinstance(adjusted, tuple)
        assert 1 <= adjusted[0] <= 12
    
    def test_adjust_oceanic(self):
        """Test oceanic climate adjustment."""
        base_window = (2, 4)
        adjusted = adjust_for_climate_zone(base_window, "oceanic")
        assert isinstance(adjusted, tuple)
        assert 1 <= adjusted[0] <= 12
    
    def test_adjust_unknown(self):
        """Test unknown climate (should return unchanged)."""
        base_window = (2, 4)
        adjusted = adjust_for_climate_zone(base_window, "unknown")
        assert adjusted == base_window
    
    def test_adjust_tropical(self):
        """Test tropical climate adjustment."""
        base_window = (3, 5)
        adjusted = adjust_for_climate_zone(base_window, "tropical")
        assert adjusted[0] <= 3  # Should extend earlier
        assert adjusted[1] >= 5  # Should extend later
    
    def test_adjust_cold(self):
        """Test cold climate adjustment."""
        base_window = (2, 4)
        adjusted = adjust_for_climate_zone(base_window, "cold")
        assert adjusted[0] >= 2  # Should start later
        assert adjusted[1] >= 4  # Should end later
    
    def test_adjust_subtropical_climate(self):
        """Test subtropical climate adjustment."""
        base_window = (2, 4)
        adjusted = adjust_for_climate_zone(base_window, "subtropical")
        assert isinstance(adjusted, tuple)
        assert len(adjusted) == 2


if __name__ == "__main__":
    pytest.main([__file__])

