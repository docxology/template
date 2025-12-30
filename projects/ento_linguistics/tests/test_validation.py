"""Comprehensive tests for src/validation.py to ensure 100% coverage."""
import sys
from pathlib import Path

import numpy as np
import pytest

# Add project src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.validation import ValidationFramework, ValidationResult


class TestValidationResult:
    """Test ValidationResult dataclass."""
    
    def test_result_creation(self):
        """Test creating validation result."""
        result = ValidationResult(
            is_valid=True,
            check_name="test_check",
            message="Test message"
        )
        assert result.is_valid is True
        assert result.check_name == "test_check"
        assert result.message == "Test message"
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        result = ValidationResult(
            is_valid=False,
            check_name="test",
            message="Error",
            severity="error"
        )
        data = result.to_dict()
        assert data["is_valid"] is False
        assert data["severity"] == "error"


class TestValidationFramework:
    """Test ValidationFramework class."""
    
    def test_initialization(self):
        """Test framework initialization."""
        validator = ValidationFramework()
        assert len(validator.validation_results) == 0
    
    def test_validate_bounds(self):
        """Test bounds validation."""
        validator = ValidationFramework()
        data = np.array([1, 2, 3, 4, 5])
        result = validator.validate_bounds(data, "test_data", min_value=0, max_value=10)
        assert result.is_valid is True
        
        # Test violation
        data = np.array([1, 2, 3, 4, 15])
        result = validator.validate_bounds(data, "test_data", min_value=0, max_value=10)
        assert result.is_valid is False
    
    def test_validate_bounds_with_range(self):
        """Test bounds validation with expected_range tuple (line 62)."""
        validator = ValidationFramework()
        data = np.array([1, 2, 3, 4, 5])
        result = validator.validate_bounds(data, "test_data", expected_range=(0, 10))
        assert result.is_valid is True
    
    def test_validate_bounds_below_minimum(self):
        """Test bounds validation with values below minimum (line 68)."""
        validator = ValidationFramework()
        data = np.array([-1, 2, 3, 4, 5])  # -1 is below minimum
        result = validator.validate_bounds(data, "test_data", min_value=0, max_value=10)
        assert result.is_valid is False
        assert "below minimum" in result.message.lower()
    
    def test_validate_sanity(self):
        """Test sanity validation."""
        validator = ValidationFramework()
        result = validator.validate_sanity(5.0, "test_value", expected_order_of_magnitude=1.0)
        assert result.is_valid is True
        
        # Test zero not allowed
        result = validator.validate_sanity(0.0, "test_value", allow_zero=False)
        assert result.is_valid is False
    
    def test_validate_sanity_negative_not_allowed(self):
        """Test sanity validation with negative value not allowed (line 120)."""
        validator = ValidationFramework()
        result = validator.validate_sanity(-5.0, "test_value", allow_negative=False)
        assert result.is_valid is False
        assert "negative" in result.message.lower()
    
    def test_validate_sanity_order_of_magnitude_violation(self):
        """Test sanity validation with order of magnitude violation (line 126)."""
        validator = ValidationFramework()
        # Value with order of magnitude very different from expected
        result = validator.validate_sanity(1e-10, "test_value", expected_order_of_magnitude=1.0)
        assert result.is_valid is False
        assert "order of magnitude" in result.message.lower()
    
    def test_validate_reproducibility(self):
        """Test reproducibility validation."""
        validator = ValidationFramework()
        run1 = {"value1": 1.0, "value2": 2.0}
        run2 = {"value1": 1.0, "value2": 2.0}
        result = validator.validate_reproducibility(run1, run2)
        assert result.is_valid is True
        
        # Test difference
        run2 = {"value1": 1.0, "value2": 3.0}
        result = validator.validate_reproducibility(run1, run2, tolerance=0.1)
        assert result.is_valid is False
    
    def test_validate_reproducibility_non_numeric(self):
        """Test reproducibility validation with non-numeric values (branch 172->168)."""
        validator = ValidationFramework()
        run1 = {"value1": "string1", "value2": 2.0}
        run2 = {"value1": "string2", "value2": 2.0}
        result = validator.validate_reproducibility(run1, run2)
        # Non-numeric values should be skipped
        assert result.is_valid is True
    
    def test_detect_anomalies(self):
        """Test anomaly detection."""
        validator = ValidationFramework()
        data = np.array([1, 2, 3, 4, 5, 100])  # 100 is an outlier
        result = validator.detect_anomalies(data, method="iqr", threshold=1.5)
        # Check that anomalies were detected (16.67% > 5% threshold)
        assert bool(result.is_valid) is False  # Too many anomalies
    
    def test_validate_quality_metrics(self):
        """Test quality metrics validation."""
        validator = ValidationFramework()
        metrics = {"accuracy": 0.9, "precision": 0.85}
        expected_ranges = {
            "accuracy": (0.8, 1.0),
            "precision": (0.7, 1.0)
        }
        results = validator.validate_quality_metrics(metrics, expected_ranges)
        assert len(results) == 2
        assert all(r.is_valid for r in results)
    
    def test_validate_quality_metrics_not_in_ranges(self):
        """Test quality metrics validation when metric not in expected_ranges (branch 257->256)."""
        validator = ValidationFramework()
        metrics = {"accuracy": 0.9, "precision": 0.85, "recall": 0.8}
        expected_ranges = {
            "accuracy": (0.8, 1.0),
            "precision": (0.7, 1.0)
            # recall is not in expected_ranges, so it should be skipped (branch 257->256)
        }
        results = validator.validate_quality_metrics(metrics, expected_ranges)
        # Should only validate metrics in expected_ranges (accuracy and precision)
        # recall should be skipped because it's not in expected_ranges
        # This covers branch 257->256 when metric_name not in expected_ranges
        assert len(results) == 2
        # Verify messages contain the metric names
        messages = [r.message for r in results]
        assert any("accuracy" in msg.lower() for msg in messages)
        assert any("precision" in msg.lower() for msg in messages)
        assert not any("recall" in msg.lower() for msg in messages)
    
    def test_generate_validation_report(self):
        """Test generating validation report."""
        validator = ValidationFramework()
        validator.validate_bounds(np.array([1, 2, 3]), "test", min_value=0, max_value=10)
        validator.validate_sanity(5.0, "test_value")
        
        report = validator.generate_validation_report()
        assert "summary" in report
        assert "results" in report
        assert report["summary"]["total_checks"] == 2
    
    def test_clear_results(self):
        """Test clearing results."""
        validator = ValidationFramework()
        validator.validate_bounds(np.array([1, 2, 3]), "test")
        assert len(validator.validation_results) > 0

        validator.clear_results()
        assert len(validator.validation_results) == 0

    def test_validate_markdown_dir(self, tmp_path):
        """Test markdown directory validation."""
        framework = ValidationFramework()

        # Create test markdown files
        manuscript_dir = tmp_path / "manuscript"
        manuscript_dir.mkdir()

        # Valid markdown file
        valid_md = manuscript_dir / "test.md"
        valid_md.write_text("""
# Test Document

Some content with a reference to [Figure @fig:test].

Also includes an equation: $$x = y + z$$

And a citation: @author2023
""")

        # Invalid markdown file with math equation issue
        invalid_md = manuscript_dir / "invalid.md"
        invalid_md.write_text("""
# Invalid Document

Use equation environment instead of $$: $$x = y + z$$
""")

        result = framework.validate_markdown_dir(str(manuscript_dir))

        assert result.is_valid is False  # Should detect issues
        problems = result.details.get("problems", [])
        assert len(problems) > 0
        assert any("missing" in error.lower() for error in problems)

    def test_validate_outputs(self, tmp_path):
        """Test output directory validation."""
        framework = ValidationFramework()

        # Create test output structure
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        figures_dir = output_dir / "figures"
        figures_dir.mkdir()

        data_dir = output_dir / "data"
        data_dir.mkdir()

        # Create some test files
        (figures_dir / "test.png").write_bytes(b"fake png data")
        (data_dir / "test.csv").write_text("col1,col2\n1,2\n3,4")

        result = framework.validate_outputs(str(output_dir))

        # Should validate successfully or provide meaningful feedback
        assert isinstance(result, ValidationResult)

    def test_validate_figure_registry(self, tmp_path):
        """Test figure registry validation."""
        framework = ValidationFramework()

        registry_file = tmp_path / "figure_registry.json"
        registry_file.write_text('{"figures": {"fig1": {"path": "test.png", "caption": "Test"}}}')

        result = framework.validate_figure_registry(str(registry_file))

        assert isinstance(result, ValidationResult)