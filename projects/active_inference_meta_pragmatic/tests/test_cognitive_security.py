"""Tests for CognitiveSecurityAnalyzer.

Validates all methods of the cognitive security analysis module
using real data and computations (no mocks).
"""

import numpy as np
import pytest
from framework.cognitive_security import CognitiveSecurityAnalyzer
from utils.exceptions import ValidationError


class TestAnalyzeAttackSurface:
    """Tests for analyze_attack_surface across all quadrants."""

    def setup_method(self):
        self.analyzer = CognitiveSecurityAnalyzer()

    def test_analyze_attack_surface_all_quadrants(self):
        """Test attack surface analysis for Q1-Q4."""
        prev_vuln = 0.0
        for q in range(1, 5):
            result = self.analyzer.analyze_attack_surface(q)

            assert result["quadrant"] == q
            assert 0.0 <= result["vulnerability_score"] <= 1.0
            assert len(result["attack_vectors"]) > 0
            assert len(result["defense_mechanisms"]) > 0
            assert 0.0 <= result["meta_level_exposure"] <= 1.0

            # Higher quadrants should have higher or equal vulnerability
            assert result["vulnerability_score"] >= prev_vuln
            prev_vuln = result["vulnerability_score"]

    def test_meta_level_exposure_increases_with_quadrant(self):
        """Q3/Q4 should have higher meta-level exposure than Q1/Q2."""
        r1 = self.analyzer.analyze_attack_surface(1)
        r2 = self.analyzer.analyze_attack_surface(2)
        r3 = self.analyzer.analyze_attack_surface(3)
        r4 = self.analyzer.analyze_attack_surface(4)

        assert r3["meta_level_exposure"] > r1["meta_level_exposure"]
        assert r4["meta_level_exposure"] > r2["meta_level_exposure"]

    def test_attack_surface_invalid_quadrant(self):
        """Test error handling for invalid quadrant numbers."""
        with pytest.raises(ValidationError, match="Quadrant must be 1-4"):
            self.analyzer.analyze_attack_surface(0)
        with pytest.raises(ValidationError, match="Quadrant must be 1-4"):
            self.analyzer.analyze_attack_surface(5)
        with pytest.raises(ValidationError, match="Quadrant must be 1-4"):
            self.analyzer.analyze_attack_surface(-1)

    def test_attack_surface_result_structure(self):
        """Verify all expected keys are present in the result."""
        result = self.analyzer.analyze_attack_surface(1)
        expected_keys = {
            "quadrant", "quadrant_name", "vulnerability_score",
            "attack_vectors", "defense_mechanisms", "meta_level_exposure",
        }
        assert set(result.keys()) == expected_keys

    def test_attack_surface_with_quadrant_framework(self):
        """Test initialization with quadrant framework reference."""
        from framework.quadrant_framework import QuadrantFramework
        qf = QuadrantFramework()
        analyzer = CognitiveSecurityAnalyzer(quadrant_framework=qf)
        result = analyzer.analyze_attack_surface(2)
        assert result["quadrant"] == 2
        assert analyzer.quadrant_framework is qf


class TestSimulateParameterDrift:
    """Tests for parameter drift simulation."""

    def setup_method(self):
        self.analyzer = CognitiveSecurityAnalyzer()

    def test_simulate_parameter_drift_basic(self):
        """Test basic drift simulation with A and D matrices."""
        params = {
            "A": np.eye(3),
            "D": np.array([1.0 / 3, 1.0 / 3, 1.0 / 3]),
        }
        result = self.analyzer.simulate_parameter_drift(params, noise_level=0.01, steps=50)

        assert "drift_trajectory" in result
        assert "total_drift" in result
        assert isinstance(result["drift_detected"], bool)
        assert result["steps"] == 50
        assert len(result["drift_trajectory"]["A"]) == 50
        assert len(result["drift_trajectory"]["D"]) == 50

    def test_drift_increases_over_time(self):
        """Drift trajectory should generally increase over time."""
        params = {"A": np.eye(4)}
        result = self.analyzer.simulate_parameter_drift(params, noise_level=0.1, steps=100)

        trajectory = result["drift_trajectory"]["A"]
        # Compare early vs late drift (later should be larger on average)
        early_mean = np.mean(trajectory[:20])
        late_mean = np.mean(trajectory[80:])
        assert late_mean > early_mean

    def test_drift_detection_high_noise(self):
        """High noise level should trigger drift detection."""
        params = {"A": np.eye(3)}
        result = self.analyzer.simulate_parameter_drift(
            params, noise_level=1.0, steps=200
        )
        assert result["total_drift"] > 0

    def test_drift_zero_noise(self):
        """Zero noise should produce zero drift."""
        params = {"A": np.eye(3)}
        result = self.analyzer.simulate_parameter_drift(
            params, noise_level=0.0, steps=50
        )
        assert result["total_drift"] == 0.0
        assert not result["drift_detected"]

    def test_drift_empty_params_raises(self):
        """Empty params dict should raise ValidationError."""
        with pytest.raises(ValidationError, match="must not be empty"):
            self.analyzer.simulate_parameter_drift({})

    def test_drift_negative_noise_raises(self):
        """Negative noise level should raise ValidationError."""
        with pytest.raises(ValidationError, match="non-negative"):
            self.analyzer.simulate_parameter_drift(
                {"A": np.eye(2)}, noise_level=-0.1
            )

    def test_drift_history_tracking(self):
        """Drift history should accumulate across calls."""
        params = {"A": np.eye(2)}
        self.analyzer.simulate_parameter_drift(params, noise_level=0.01, steps=10)
        self.analyzer.simulate_parameter_drift(params, noise_level=0.01, steps=10)
        assert len(self.analyzer._drift_history) == 2


class TestDetectAnomaly:
    """Tests for belief state anomaly detection."""

    def setup_method(self):
        self.analyzer = CognitiveSecurityAnalyzer()

    def test_detect_anomaly_identical_distributions(self):
        """Identical distributions should have zero KL divergence."""
        beliefs = np.array([0.5, 0.3, 0.2])
        result = self.analyzer.detect_anomaly(beliefs, beliefs.copy())
        assert not result["is_anomalous"]
        assert result["kl_divergence"] < 1e-8
        assert result["severity"] == "low"

    def test_detect_anomaly_different_distributions(self):
        """Very different distributions should be flagged as anomalous."""
        beliefs = np.array([0.9, 0.05, 0.05])
        baseline = np.array([0.1, 0.45, 0.45])
        result = self.analyzer.detect_anomaly(beliefs, baseline, threshold=0.05)
        assert result["is_anomalous"]
        assert result["kl_divergence"] > 0.05

    def test_detect_anomaly_severity_levels(self):
        """Test that severity escalates with increasing divergence."""
        baseline = np.array([1.0 / 3, 1.0 / 3, 1.0 / 3])
        threshold = 0.01

        # Near-identical should be low
        near = np.array([0.34, 0.33, 0.33])
        r1 = self.analyzer.detect_anomaly(near, baseline, threshold=threshold)

        # Very different should be high or critical
        far = np.array([0.98, 0.01, 0.01])
        r2 = self.analyzer.detect_anomaly(far, baseline, threshold=threshold)

        # The far case should have higher severity
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        assert severity_order[r2["severity"]] >= severity_order[r1["severity"]]

    def test_detect_anomaly_uniform_distributions(self):
        """Uniform distributions compared should show low divergence."""
        uniform = np.array([0.25, 0.25, 0.25, 0.25])
        result = self.analyzer.detect_anomaly(uniform, uniform.copy())
        assert not result["is_anomalous"]
        assert result["severity"] == "low"

    def test_detect_anomaly_shape_mismatch_raises(self):
        """Mismatched array shapes should raise ValidationError."""
        with pytest.raises(ValidationError, match="shape"):
            self.analyzer.detect_anomaly(
                np.array([0.5, 0.5]),
                np.array([0.33, 0.33, 0.34]),
            )

    def test_detect_anomaly_2d_raises(self):
        """2-D arrays should raise ValidationError."""
        with pytest.raises(ValidationError, match="1-D"):
            self.analyzer.detect_anomaly(
                np.eye(3), np.eye(3)
            )

    def test_detect_anomaly_zero_entries_handled(self):
        """Distributions with zero entries should be handled (clipped)."""
        beliefs = np.array([1.0, 0.0, 0.0])
        baseline = np.array([0.0, 0.5, 0.5])
        result = self.analyzer.detect_anomaly(beliefs, baseline)
        assert np.isfinite(result["kl_divergence"])
        assert result["is_anomalous"]


class TestValidateFrameworkIntegrity:
    """Tests for framework integrity validation."""

    def setup_method(self):
        self.analyzer = CognitiveSecurityAnalyzer()

    def _valid_params(self):
        """Create a valid set of model parameters."""
        A = np.array([
            [0.8, 0.1, 0.1],
            [0.1, 0.8, 0.1],
            [0.1, 0.1, 0.8],
        ])
        B = np.zeros((3, 3, 2))
        B[:, :, 0] = np.array([
            [0.9, 0.05, 0.05],
            [0.05, 0.9, 0.05],
            [0.05, 0.05, 0.9],
        ])
        B[:, :, 1] = np.array([
            [0.1, 0.45, 0.45],
            [0.45, 0.1, 0.45],
            [0.45, 0.45, 0.1],
        ])
        C = np.array([2.0, 0.0, -2.0])
        D = np.array([1.0 / 3, 1.0 / 3, 1.0 / 3])
        return {"A": A, "B": B, "C": C, "D": D}

    def test_validate_valid_model(self):
        """Valid model should pass all checks."""
        result = self.analyzer.validate_framework_integrity(self._valid_params())
        assert result["is_valid"]
        assert len(result["issues"]) == 0
        assert result["integrity_score"] == 1.0

    def test_validate_tampered_A_negative(self):
        """A matrix with negative values should fail."""
        params = self._valid_params()
        params["A"][0, 0] = -0.5
        result = self.analyzer.validate_framework_integrity(params)
        assert not result["is_valid"]
        assert any("negative" in issue.lower() for issue in result["issues"])

    def test_validate_tampered_A_not_stochastic(self):
        """A matrix with columns not summing to 1 should fail."""
        params = self._valid_params()
        params["A"][:, 0] = [0.5, 0.1, 0.1]  # sum = 0.7
        result = self.analyzer.validate_framework_integrity(params)
        assert not result["is_valid"]
        assert any("sum to 1" in issue.lower() for issue in result["issues"])

    def test_validate_tampered_D_not_normalized(self):
        """D matrix not summing to 1 should fail."""
        params = self._valid_params()
        params["D"] = np.array([0.5, 0.5, 0.5])  # sum = 1.5
        result = self.analyzer.validate_framework_integrity(params)
        assert not result["is_valid"]
        assert any("D matrix" in issue for issue in result["issues"])

    def test_validate_tampered_C_inf(self):
        """C matrix with inf values should fail."""
        params = self._valid_params()
        params["C"][0] = np.inf
        result = self.analyzer.validate_framework_integrity(params)
        assert not result["is_valid"]
        assert any("non-finite" in issue.lower() for issue in result["issues"])

    def test_validate_missing_matrix_raises(self):
        """Missing required matrix should raise ValidationError."""
        params = self._valid_params()
        del params["B"]
        with pytest.raises(ValidationError, match="Missing required"):
            self.analyzer.validate_framework_integrity(params)

    def test_validate_dimension_mismatch(self):
        """Incompatible A/D dimensions should fail."""
        params = self._valid_params()
        params["D"] = np.array([0.5, 0.5])  # 2 states but A expects 3
        result = self.analyzer.validate_framework_integrity(params)
        assert not result["is_valid"]
        assert result["integrity_score"] < 1.0

    def test_integrity_score_partial(self):
        """Integrity score should reflect fraction of passed checks."""
        params = self._valid_params()
        # Tamper with D normalization only
        params["D"] = np.array([0.6, 0.3, 0.2])  # sum = 1.1
        result = self.analyzer.validate_framework_integrity(params)
        assert 0.0 < result["integrity_score"] < 1.0

    def test_validate_1d_A_matrix(self):
        """1-D A matrix should fail stochasticity check."""
        params = self._valid_params()
        params["A"] = np.array([0.5, 0.3, 0.2])
        result = self.analyzer.validate_framework_integrity(params)
        assert not result["is_valid"]
        assert any("not 2-dimensional" in issue for issue in result["issues"])

    def test_validate_B_negative_values(self):
        """B matrix with negative values should fail."""
        params = self._valid_params()
        params["B"][0, 0, 0] = -0.1
        result = self.analyzer.validate_framework_integrity(params)
        assert not result["is_valid"]
        assert any("B matrix" in issue and "negative" in issue for issue in result["issues"])

    def test_validate_D_negative(self):
        """D matrix with negative values should fail."""
        params = self._valid_params()
        params["D"] = np.array([-0.1, 0.6, 0.5])
        result = self.analyzer.validate_framework_integrity(params)
        assert not result["is_valid"]

    def test_validate_2d_B_matrix(self):
        """2-D B matrix should be handled."""
        params = self._valid_params()
        params["B"] = np.eye(3)  # 2D instead of 3D
        result = self.analyzer.validate_framework_integrity(params)
        # Should still validate (2D B is accepted)
        assert "B_stochastic" in result["checks"]

    def test_validate_B_not_stochastic(self):
        """B matrix with columns not summing to 1 should fail."""
        params = self._valid_params()
        params["B"][:, :, 0] = np.ones((3, 3))  # columns sum to 3
        result = self.analyzer.validate_framework_integrity(params)
        assert not result["is_valid"]

    def test_validate_AC_dimension_mismatch(self):
        """Incompatible A/C dimensions should fail."""
        params = self._valid_params()
        params["C"] = np.array([1.0, 0.0])  # 2 obs but A has 3
        result = self.analyzer.validate_framework_integrity(params)
        assert not result["is_valid"]
        assert any("A rows" in issue for issue in result["issues"])


class TestEdgeCases:
    """Edge case tests for cognitive security."""

    def setup_method(self):
        self.analyzer = CognitiveSecurityAnalyzer()

    def test_drift_invalid_steps(self):
        """Steps < 1 should raise ValidationError."""
        with pytest.raises(ValidationError, match="steps must be >= 1"):
            self.analyzer.simulate_parameter_drift(
                {"A": np.eye(2)}, steps=0
            )

    def test_detect_anomaly_critical_severity(self):
        """Very different distributions should be classified as critical."""
        # Use a very small threshold so even moderate difference is critical
        beliefs = np.array([0.99, 0.005, 0.005])
        baseline = np.array([0.005, 0.005, 0.99])
        result = self.analyzer.detect_anomaly(
            beliefs, baseline, threshold=0.001
        )
        assert result["severity"] == "critical"

    def test_detect_anomaly_high_severity(self):
        """Moderately different distributions with low threshold should be high."""
        baseline = np.array([1.0 / 3, 1.0 / 3, 1.0 / 3])
        beliefs = np.array([0.6, 0.2, 0.2])
        result = self.analyzer.detect_anomaly(
            beliefs, baseline, threshold=0.01
        )
        assert result["severity"] in ("high", "critical")
