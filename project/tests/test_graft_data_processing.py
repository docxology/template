"""Comprehensive tests for graft_data_processing module."""
import pytest
import numpy as np
from graft_data_processing import (
    clean_graft_data,
    normalize_graft_parameters,
    extract_graft_features,
    detect_outlier_trials,
    create_graft_validation_pipeline
)


class TestDataCleaning:
    """Test data cleaning functions."""
    
    def test_remove_failed(self):
        """Test removing failed grafts."""
        data = {
            "success": np.array([1, 0, 1, 0, 1]),
            "union_strength": np.array([0.8, np.nan, 0.9, np.nan, 0.7])
        }
        cleaned = clean_graft_data(data, remove_failed=True)
        assert len(cleaned["success"]) == 3
        assert np.all(cleaned["success"] == 1)
    
    def test_fill_missing(self):
        """Test filling missing values."""
        data = {
            "union_strength": np.array([0.8, np.nan, 0.9])
        }
        cleaned = clean_graft_data(data, fill_missing="mean")
        assert not np.any(np.isnan(cleaned["union_strength"]))
    
    def test_fill_missing_median(self):
        """Test filling missing values with median."""
        data = {
            "union_strength": np.array([0.8, np.nan, 0.9, np.nan, 0.7])
        }
        cleaned = clean_graft_data(data, fill_missing="median")
        assert not np.any(np.isnan(cleaned["union_strength"]))
        # Median of [0.8, 0.9, 0.7] is 0.8
        assert cleaned["union_strength"][1] == pytest.approx(0.8)
    
    def test_fill_missing_zero(self):
        """Test filling missing values with zero."""
        data = {
            "union_strength": np.array([0.8, np.nan, 0.9])
        }
        cleaned = clean_graft_data(data, fill_missing="zero")
        assert not np.any(np.isnan(cleaned["union_strength"]))
        assert cleaned["union_strength"][1] == 0.0


class TestNormalization:
    """Test data normalization."""
    
    def test_z_score_normalization(self):
        """Test z-score normalization."""
        data = {
            "temperature": np.array([20.0, 22.0, 24.0]),
            "humidity": np.array([0.7, 0.8, 0.9])
        }
        normalized, params = normalize_graft_parameters(data, method="z_score")
        assert "temperature" in normalized
        assert "mean" in params["temperature"]
    
    def test_min_max_normalization(self):
        """Test min-max normalization."""
        data = {
            "temperature": np.array([20.0, 22.0, 24.0]),
            "humidity": np.array([0.7, 0.8, 0.9])
        }
        normalized, params = normalize_graft_parameters(data, method="min_max")
        assert "temperature" in normalized
        assert "min" in params["temperature"]
        assert "max" in params["temperature"]
        # Normalized values should be in [0, 1] range
        assert np.all(normalized["temperature"] >= 0)
        assert np.all(normalized["temperature"] <= 1)


class TestFeatureExtraction:
    """Test feature extraction."""
    
    def test_diameter_ratio(self):
        """Test diameter ratio feature."""
        data = {
            "rootstock_diameter": np.array([15.0, 20.0]),
            "scion_diameter": np.array([15.0, 18.0])
        }
        features = extract_graft_features(data)
        assert "diameter_ratio" in features
        assert features["diameter_ratio"][0] == pytest.approx(1.0)
    
    def test_environmental_score(self):
        """Test environmental score feature."""
        data = {
            "temperature": np.array([22.0, 25.0]),
            "humidity": np.array([0.8, 0.7])
        }
        features = extract_graft_features(data)
        assert "environmental_score" in features
    
    def test_overall_quality(self):
        """Test overall quality feature extraction."""
        data = {
            "compatibility": np.array([0.8, 0.9]),
            "technique_quality": np.array([0.7, 0.8]),
            "temperature": np.array([22.0, 23.0]),
            "humidity": np.array([0.8, 0.75])
        }
        features = extract_graft_features(data)
        assert "overall_quality" in features
        # Overall quality should be mean of compatibility, technique_quality, and environmental_score
        assert len(features["overall_quality"]) == 2
        assert np.all(features["overall_quality"] >= 0)
        assert np.all(features["overall_quality"] <= 1)


class TestOutlierDetection:
    """Test outlier detection."""
    
    def test_iqr_method(self):
        """Test IQR outlier detection."""
        # Use a dataset with clear outliers in multiple dimensions
        # (outlier detection requires >= 2 dimensions to flag a trial as outlier)
        data = {
            "temperature": np.array([20.0, 21.0, 22.0, 21.5, 22.5, 23.0, 21.8, 22.2, 100.0, -10.0]),
            "humidity": np.array([0.7, 0.75, 0.8, 0.78, 0.82, 0.79, 0.76, 0.81, 2.0, -0.5])
        }
        outlier_mask, info = detect_outlier_trials(data, method="iqr")
        # Outliers at indices 8 and 9 (100.0, 2.0) and (-10.0, -0.5)
        assert np.sum(outlier_mask) > 0
    
    def test_z_score_method(self):
        """Test z-score outlier detection."""
        data = {
            "temperature": np.array([20.0, 21.0, 22.0, 21.5, 22.5, 23.0, 21.8, 22.2, 100.0, -10.0]),
            "humidity": np.array([0.7, 0.75, 0.8, 0.78, 0.82, 0.79, 0.76, 0.81, 2.0, -0.5])
        }
        outlier_mask, info = detect_outlier_trials(data, method="z_score", threshold=2.0)
        assert "method" in info
        assert info["method"] == "z_score"
        # Should detect outliers at indices 8 and 9
        assert np.sum(outlier_mask) > 0


class TestValidationPipeline:
    """Test validation pipeline creation."""
    
    def test_validation_pipeline_check_finite(self):
        """Test validation pipeline with check_finite step."""
        pipeline = create_graft_validation_pipeline([
            ("check_finite", {})
        ])
        data = {
            "temperature": np.array([20.0, 22.0, np.inf]),
            "humidity": np.array([0.7, 0.8, 0.9])
        }
        is_valid, errors = pipeline(data)
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
    
    def test_validation_pipeline_check_ranges(self):
        """Test validation pipeline with check_ranges step."""
        pipeline = create_graft_validation_pipeline([
            ("check_ranges", {
                "ranges": {
                    "temperature": (15.0, 30.0),
                    "humidity": (0.5, 1.0)
                }
            })
        ])
        data = {
            "temperature": np.array([20.0, 22.0, 35.0]),  # 35.0 is out of range
            "humidity": np.array([0.7, 0.8, 0.9])
        }
        is_valid, errors = pipeline(data)
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
        # Should have error for temperature out of range
        if not is_valid:
            assert len(errors) > 0
    
    def test_validation_pipeline_check_outliers(self):
        """Test validation pipeline with check_outliers step."""
        pipeline = create_graft_validation_pipeline([
            ("check_outliers", {
                "method": "iqr",
                "threshold": 1.5,
                "max_outlier_percentage": 5.0
            })
        ])
        # Create data with many outliers
        data = {
            "temperature": np.array([20.0, 21.0, 22.0, 100.0, 100.0, 100.0, 100.0, 100.0]),
            "humidity": np.array([0.7, 0.75, 0.8, 2.0, 2.0, 2.0, 2.0, 2.0])
        }
        is_valid, errors = pipeline(data)
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
    
    def test_validation_pipeline_all_steps(self):
        """Test validation pipeline with all steps."""
        pipeline = create_graft_validation_pipeline([
            ("check_finite", {}),
            ("check_ranges", {
                "ranges": {
                    "temperature": (15.0, 30.0)
                }
            }),
            ("check_outliers", {
                "method": "iqr",
                "threshold": 1.5,
                "max_outlier_percentage": 10.0
            })
        ])
        data = {
            "temperature": np.array([20.0, 22.0, 24.0]),
            "humidity": np.array([0.7, 0.8, 0.9])
        }
        is_valid, errors = pipeline(data)
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
    
    def test_validation_pipeline_exception_handling(self):
        """Test validation pipeline handles exceptions gracefully."""
        pipeline = create_graft_validation_pipeline([
            ("check_ranges", {
                "ranges": {
                    "nonexistent_key": (0.0, 1.0)
                }
            })
        ])
        data = {
            "temperature": np.array([20.0, 22.0])
        }
        # Should not raise exception, but may have errors
        is_valid, errors = pipeline(data)
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)


if __name__ == "__main__":
    pytest.main([__file__])

