"""Integration tests for the active_inference_meta_pragmatic framework.

Tests end-to-end workflows across multiple modules without mocks.
All tests use real data and computations.
"""

import numpy as np
import pytest
from pathlib import Path

from core.active_inference import ActiveInferenceFramework
from core.generative_models import GenerativeModel, create_simple_generative_model
from core.free_energy_principle import FreeEnergyPrinciple
from framework.quadrant_framework import QuadrantFramework
from framework.meta_cognition import MetaCognitiveSystem
from framework.cognitive_security import CognitiveSecurityAnalyzer
from analysis.data_generator import DataGenerator
from analysis.statistical_analysis import StatisticalAnalyzer
from analysis.validation import ValidationFramework
from visualization import VisualizationEngine


class TestEndToEndQuadrantAnalysis:
    """Test complete quadrant analysis pipeline from model creation to EFE computation."""

    def test_full_quadrant_analysis(self, simple_generative_model):
        """Create generative model, analyze all 4 quadrants, verify EFE values."""
        model = simple_generative_model
        framework = ActiveInferenceFramework(generative_model=model)
        quadrant = QuadrantFramework()

        # Compute EFE for a simple policy
        posterior = np.array([0.7, 0.2, 0.1])
        policy = np.array([0])
        efe, components = framework.calculate_expected_free_energy(posterior, policy)

        # Verify EFE is finite and real
        assert np.isfinite(efe)
        assert isinstance(efe, float)

        # Analyze all quadrants
        for qid in ["Q1_data_cognitive", "Q2_metadata_cognitive",
                     "Q3_data_metacognitive", "Q4_metadata_metacognitive"]:
            q_info = quadrant.get_quadrant(qid)
            assert "name" in q_info
            assert "description" in q_info

        # Verify matrix data from quadrant framework
        matrix_data = quadrant.create_quadrant_matrix_visualization()
        assert matrix_data is not None


class TestMetaCognitiveQuadrantIntegration:
    """Test meta-cognitive processing integrated with quadrant framework."""

    def test_meta_cognitive_quadrant_integration(
        self, meta_cognitive_system, sample_posterior_beliefs
    ):
        """Test meta-cognition evaluating beliefs at different quadrant levels."""
        system = meta_cognitive_system

        # Assess confidence for different belief configurations
        assessments = {}
        for name, beliefs in sample_posterior_beliefs.items():
            assessment = system.assess_inference_confidence(
                beliefs, observation_uncertainty=0.2
            )
            assessments[name] = assessment
            assert "confidence_score" in assessment
            assert 0.0 <= assessment["confidence_score"] <= 1.0

        # Confident beliefs should have higher confidence score than uncertain
        assert (
            assessments["confident"]["confidence_score"]
            > assessments["uncertain"]["confidence_score"]
        )

        # Attention allocation should shift based on confidence
        resources = {"monitoring": 1.0, "processing": 1.0, "evaluation": 1.0}
        for name, assessment in assessments.items():
            allocation = system.adjust_attention_allocation(assessment, resources)
            assert abs(sum(allocation.values()) - 1.0) < 1e-6


class TestDataToStatisticsPipeline:
    """Test data generation feeding into statistical analysis."""

    def test_data_to_statistics_pipeline(self):
        """Generate synthetic data and run statistical analysis end-to-end."""
        gen = DataGenerator(seed=42)
        analyzer = StatisticalAnalyzer(alpha=0.05)

        # Generate time series data
        values = gen.generate_time_series(n_points=200, noise_level=0.1)
        assert len(values) == 200

        # Run descriptive statistics
        desc = analyzer.calculate_descriptive_stats(values)
        assert "mean" in desc
        assert "std" in desc
        assert "count" in desc
        assert desc["count"] == 200

        # Generate two groups and compare
        group1 = gen.generate_time_series(n_points=100, noise_level=0.1)
        group2 = gen.generate_time_series(n_points=100, noise_level=0.5)

        # T-test between groups
        t_result = analyzer.perform_t_test(group1, group2, test_type="independent")
        assert "t_statistic" in t_result
        assert "p_value" in t_result
        assert isinstance(t_result["significant"], (bool, np.bool_))


class TestFrameworkValidationIntegration:
    """Test validation module across all src modules."""

    def test_framework_validation_integration(self, simple_generative_model):
        """Validate model, run inference, and verify results."""
        model = simple_generative_model
        validator = ValidationFramework(tolerance=1e-6)

        # Validate D as probability distribution
        d_result = validator.validate_probability_distribution(model.D, name="D_prior")
        assert d_result["valid"]

        # Validate each column of A
        for col_idx in range(model.A.shape[1]):
            a_result = validator.validate_probability_distribution(
                model.A[:, col_idx], name=f"A_col_{col_idx}"
            )
            assert a_result["valid"]

        # Run inference and validate output
        framework = ActiveInferenceFramework(generative_model=model)
        posterior = np.array([0.5, 0.3, 0.2])
        policy = np.array([0])
        efe, components = framework.calculate_expected_free_energy(posterior, policy)
        assert np.isfinite(efe)


class TestFigureGenerationIntegration:
    """Test visualization produces valid output files."""

    def test_figure_generation_produces_valid_png(self, output_dir):
        """Test that visualization produces valid PNG files."""
        viz = VisualizationEngine(output_dir=str(output_dir))

        # Create a simple figure (returns (fig, ax) tuple)
        fig, ax = viz.create_figure(figsize=(8, 6))
        import matplotlib.pyplot as plt
        ax.plot([1, 2, 3], [1, 4, 9])
        ax.set_title("Integration Test Figure")

        # Save figure
        saved = viz.save_figure(fig, "integration_test")

        # Verify file exists and has content
        png_path = Path(saved["png"])
        assert png_path.exists()
        assert png_path.stat().st_size > 0

        plt.close(fig)

    def test_quadrant_matrix_visualization(self, output_dir):
        """Test quadrant matrix plot generation."""
        qf = QuadrantFramework()
        viz = VisualizationEngine(output_dir=str(output_dir))

        matrix_data = qf.create_quadrant_matrix_visualization()
        fig = viz.create_quadrant_matrix_plot(matrix_data)

        saved = viz.save_figure(fig, "quadrant_test")
        assert Path(saved["png"]).exists()

        import matplotlib.pyplot as plt
        plt.close(fig)


class TestCognitiveSecurityIntegration:
    """Test cognitive security analyzer with real model parameters."""

    def test_security_analysis_with_real_model(self, simple_generative_model):
        """Analyze security of a real generative model."""
        model = simple_generative_model
        analyzer = CognitiveSecurityAnalyzer()

        # Validate framework integrity
        params = {
            "A": model.A,
            "B": model.B,
            "C": model.C,
            "D": model.D,
        }
        integrity = analyzer.validate_framework_integrity(params)
        assert integrity["is_valid"]

        # Simulate drift on model parameters
        drift = analyzer.simulate_parameter_drift(
            params, noise_level=0.01, steps=50
        )
        assert drift["total_drift"] >= 0

        # Detect anomaly in beliefs
        normal_beliefs = np.array([0.6, 0.3, 0.1])
        baseline = model.D
        anomaly = analyzer.detect_anomaly(normal_beliefs, baseline, threshold=0.1)
        assert "is_anomalous" in anomaly
        assert "severity" in anomaly
