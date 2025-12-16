"""Comprehensive tests for graft_data_generator module."""
import pytest
import numpy as np
from graft_data_generator import (
    generate_graft_trial_data,
    generate_compatibility_matrix,
    generate_environmental_data,
    generate_success_scenarios,
    validate_graft_data
)


class TestGraftTrialData:
    """Test graft trial data generation."""
    
    def test_basic_generation(self):
        """Test basic trial data generation."""
        data = generate_graft_trial_data(100, n_species=10, seed=42)
        assert len(data["success"]) == 100
        assert len(data["rootstock_species"]) == 100
        assert np.all(data["success"] >= 0) and np.all(data["success"] <= 1)
    
    def test_success_rate(self):
        """Test success rate in generated data."""
        data = generate_graft_trial_data(1000, success_rate=0.8, seed=42)
        actual_rate = np.mean(data["success"])
        assert 0.7 <= actual_rate <= 0.9  # Allow some variance
    
    def test_data_structure(self):
        """Test data structure completeness."""
        data = generate_graft_trial_data(50, seed=42)
        required_keys = ["success", "compatibility", "temperature", "humidity", "union_strength"]
        for key in required_keys:
            assert key in data


class TestCompatibilityMatrix:
    """Test compatibility matrix generation."""
    
    def test_matrix_shape(self):
        """Test matrix shape."""
        matrix = generate_compatibility_matrix(20, seed=42)
        assert matrix.shape == (20, 20)
        assert np.all(matrix >= 0) and np.all(matrix <= 1)
    
    def test_self_compatibility(self):
        """Test self-compatibility is 1.0."""
        matrix = generate_compatibility_matrix(10, seed=42)
        assert np.all(np.diag(matrix) == 1.0)
    
    def test_symmetry(self):
        """Test matrix symmetry."""
        matrix = generate_compatibility_matrix(10, seed=42)
        assert np.allclose(matrix, matrix.T)
    
    def test_compatibility_matrix_no_phylogeny(self):
        """Test compatibility matrix without phylogenetic structure."""
        matrix = generate_compatibility_matrix(10, phylogenetic_structure=False, seed=42)
        assert matrix.shape == (10, 10)
        assert np.all(np.diag(matrix) == 1.0)
        assert np.allclose(matrix, matrix.T)


class TestEnvironmentalData:
    """Test environmental data generation."""
    
    def test_seasonal_data(self):
        """Test seasonal environmental data."""
        data = generate_environmental_data(100, season="spring", seed=42)
        assert len(data["temperature"]) == 100
        assert np.all(data["humidity"] >= 0) and np.all(data["humidity"] <= 1)
    
    def test_temperature_range(self):
        """Test temperature ranges by season."""
        spring_data = generate_environmental_data(100, season="spring", seed=42)
        winter_data = generate_environmental_data(100, season="winter", seed=43)
        assert np.mean(spring_data["temperature"]) > np.mean(winter_data["temperature"])
    
    def test_environmental_data_summer(self):
        """Test summer environmental data."""
        data = generate_environmental_data(100, season="summer", seed=42)
        assert "temperature" in data
        assert "humidity" in data
        assert "light_hours" in data
        assert "rainfall" in data
        assert np.mean(data["temperature"]) > 20.0  # Summer is warmer
    
    def test_environmental_data_fall(self):
        """Test fall environmental data."""
        data = generate_environmental_data(100, season="fall", seed=42)
        assert len(data["temperature"]) == 100
        assert np.all(data["humidity"] >= 0) and np.all(data["humidity"] <= 1)
    
    def test_environmental_data_unknown_season(self):
        """Test environmental data with unknown season."""
        data = generate_environmental_data(100, season="unknown", seed=42)
        assert "temperature" in data
        assert len(data["temperature"]) == 100


class TestDataValidation:
    """Test data validation."""
    
    def test_valid_data(self):
        """Test validation of valid data."""
        data = {
            "compatibility": np.array([0.7, 0.8, 0.9]),
            "humidity": np.array([0.7, 0.8, 0.9]),
            "success": np.array([1, 1, 0])
        }
        is_valid, error = validate_graft_data(data)
        assert is_valid is True
    
    def test_invalid_ranges(self):
        """Test validation catches invalid ranges."""
        data = {
            "compatibility": np.array([1.5, 0.8]),  # Out of range
            "humidity": np.array([0.7, 0.8])
        }
        is_valid, error = validate_graft_data(data, check_ranges=True)
        assert is_valid is False
    
    def test_validate_no_checks(self):
        """Test validation with checks disabled."""
        data = {
            "compatibility": np.array([1.5, 0.8]),  # Out of range
            "humidity": np.array([0.7, 0.8])
        }
        is_valid, error = validate_graft_data(data, check_finite=False, check_ranges=False)
        assert is_valid is True  # Should pass if checks disabled
    
    def test_validate_non_finite(self):
        """Test validation catches non-finite values."""
        data = {
            "compatibility": np.array([0.8, np.inf, 0.9]),
            "humidity": np.array([0.7, 0.8, 0.9])
        }
        is_valid, error = validate_graft_data(data, check_finite=True)
        assert is_valid is False
        assert "Non-finite" in error
    
    def test_validate_temperature_range(self):
        """Test validation catches temperature out of range."""
        data = {
            "temperature": np.array([60.0, 22.0]),  # 60 is > 50
            "humidity": np.array([0.7, 0.8])
        }
        is_valid, error = validate_graft_data(data, check_ranges=True)
        assert is_valid is False
        assert "temperature" in error.lower()
    
    def test_validate_with_nans(self):
        """Test validation handles NaN values correctly."""
        data = {
            "compatibility": np.array([0.8, np.nan, 0.9]),
            "humidity": np.array([0.7, 0.8, 0.9])
        }
        is_valid, error = validate_graft_data(data, check_ranges=True)
        # Should pass - NaN values are filtered out
        assert is_valid is True


class TestSuccessScenarios:
    """Test success scenario generation."""
    
    def test_generate_success_scenarios(self):
        """Test generating success scenarios."""
        scenarios = generate_success_scenarios(5, base_success_rate=0.8, seed=42)
        assert "scenario_id" in scenarios
        assert "success" in scenarios
        assert "scenario_success_rates" in scenarios
        assert "trials_per_scenario" in scenarios
        assert len(scenarios["scenario_success_rates"]) == 5
    
    def test_success_scenarios_minimum_trials(self):
        """Test that scenarios have minimum 10 trials."""
        scenarios = generate_success_scenarios(3, base_success_rate=0.7, seed=42)
        assert np.all(scenarios["trials_per_scenario"] >= 10)


if __name__ == "__main__":
    pytest.main([__file__])

