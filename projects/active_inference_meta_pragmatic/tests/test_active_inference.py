"""Tests for Active Inference Framework.

Comprehensive tests for the Active Inference implementation, including EFE calculations,
policy selection, perception as inference, and theoretical correctness validation.
"""

import numpy as np
import pytest

from infrastructure.core.exceptions import ValidationError

from src.active_inference import ActiveInferenceFramework, demonstrate_active_inference_concepts
from src.generative_models import create_simple_generative_model
from src.validation import ValidationFramework


class TestActiveInferenceFramework:
    """Test Active Inference framework core functionality."""

    @pytest.fixture
    def simple_model(self):
        """Create a simple generative model for testing."""
        return create_simple_generative_model()

    @pytest.fixture
    def framework(self, simple_model):
        """Create Active Inference framework instance."""
        return ActiveInferenceFramework(simple_model)

    def test_initialization(self, framework, simple_model):
        """Test framework initialization."""
        assert framework.generative_model is not None
        assert framework.precision == 1.0
        assert framework.n_states == simple_model.n_states
        assert framework.n_observations == simple_model.n_observations

    def test_calculate_expected_free_energy(self, framework):
        """Test EFE calculation."""
        posterior_beliefs = np.array([0.6, 0.4])
        policy = np.array([0])  # Single action

        efe_total, efe_components = framework.calculate_expected_free_energy(
            posterior_beliefs, policy
        )

        assert isinstance(efe_total, (int, float))
        assert 'epistemic' in efe_components
        assert 'pragmatic' in efe_components
        assert 'total' in efe_components
        assert efe_components['total'] == efe_total

    def test_policy_selection(self, framework):
        """Test optimal policy selection."""
        candidate_policies = [np.array([0]), np.array([1])]

        optimal_policy, selection_info = framework.select_optimal_policy(candidate_policies)

        assert optimal_policy in candidate_policies
        assert 'optimal_policy' in selection_info
        assert 'all_scores' in selection_info
        assert len(selection_info['all_scores']) == len(candidate_policies)

    def test_perception_as_inference(self, framework):
        """Test perception as inference."""
        observations = np.array([0.8, 0.2])

        posterior = framework.perception_as_inference(observations)

        # Should return valid probability distribution
        assert len(posterior) == framework.n_states
        assert np.all(posterior >= 0)
        assert np.isclose(np.sum(posterior), 1.0, atol=1e-6)

    def test_error_handling(self, framework):
        """Test error handling for invalid inputs."""
        with pytest.raises(Exception):
            framework.calculate_expected_free_energy(
                np.array([-0.1, 1.1]),  # Invalid probabilities
                np.array([0])
            )


class TestActiveInferenceConcepts:
    """Test Active Inference conceptual demonstrations."""

    def test_demonstrate_concepts(self):
        """Test conceptual demonstration function."""
        concepts = demonstrate_active_inference_concepts()

        assert 'concepts' in concepts
        assert 'numerical_example' in concepts

        # Check key concepts are present
        required_concepts = [
            'perception_as_inference',
            'expected_free_energy',
            'generative_models',
            'meta_pragmatic_aspect',
            'meta_epistemic_aspect'
        ]

        for concept in required_concepts:
            assert concept in concepts['concepts']

    def test_numerical_correctness(self):
        """Test numerical correctness of demonstrations."""
        concepts = demonstrate_active_inference_concepts()

        numerical = concepts['numerical_example']

        # Check EFE components are reasonable
        efe_components = numerical['efe_components']
        assert 'epistemic' in efe_components
        assert 'pragmatic' in efe_components
        assert 'total' in efe_components

        # Check posterior beliefs form valid distribution
        posterior = np.array(numerical['posterior_beliefs'])
        assert np.all(posterior >= 0)
        assert np.isclose(np.sum(posterior), 1.0, atol=1e-6)


class TestTheoreticalValidation:
    """Test theoretical correctness validation."""

    @pytest.fixture
    def validator(self):
        """Create validation framework instance."""
        return ValidationFramework()

    def test_theoretical_correctness_validation(self, validator):
        """Test theoretical correctness validation."""
        # Create test results
        implementation_result = {
            'efe_components': {
                'epistemic': 0.3,
                'pragmatic': 0.7,
                'total': 1.0
            },
            'posterior_beliefs': np.array([0.6, 0.4])
        }

        theoretical_expectation = {
            'efe_expectation': {
                'epistemic_range': [0, 2],
                'pragmatic_range': [0, 2]
            },
            'inference_expectation': {
                'distribution_valid': True
            }
        }

        result = validator.validate_theoretical_correctness(
            'active_inference_test',
            implementation_result,
            theoretical_expectation
        )

        assert 'overall_correctness' in result
        assert 'theoretical_checks' in result
        assert 'implementation_checks' in result

    def test_algorithm_performance_validation(self, validator):
        """Test algorithm performance validation."""
        performance_metrics = {
            'accuracy': 0.85,
            'efficiency': 0.92,
            'convergence_rate': 0.78
        }

        requirements = {
            'accuracy': 0.8,
            'efficiency': (0.85, 0.95),  # Range requirement
            'convergence_rate': 0.7
        }

        result = validator.validate_algorithm_performance(
            performance_metrics, requirements
        )

        assert 'overall_pass' in result
        assert 'metric_validations' in result
        assert 'requirements_met' in result

    def test_probability_distribution_validation(self, validator):
        """Test probability distribution validation."""
        # Valid distribution
        valid_dist = np.array([0.3, 0.4, 0.3])
        result = validator.validate_probability_distribution(valid_dist)
        assert result['valid'] is True

        # Invalid distribution (negative values)
        invalid_dist = np.array([0.3, -0.1, 0.8])
        with pytest.raises(Exception):
            validator.validate_probability_distribution(invalid_dist)

        # Invalid distribution (doesn't sum to 1)
        invalid_dist2 = np.array([0.3, 0.4, 0.4])
        with pytest.raises(Exception):
            validator.validate_probability_distribution(invalid_dist2)


class TestGenerativeModelIntegration:
    """Test integration with generative models."""

    def test_model_framework_integration(self):
        """Test integration between generative models and Active Inference."""
        model = create_simple_generative_model()
        framework = ActiveInferenceFramework(model)

        # Test that framework can use model predictions
        observation = np.array([1.0, 0.0])
        posterior = framework.perception_as_inference(observation)

        assert len(posterior) == model.n_states
        assert np.all(posterior >= 0)
        assert np.isclose(np.sum(posterior), 1.0)

    def test_policy_evaluation_with_model(self):
        """Test policy evaluation using generative model."""
        model = create_simple_generative_model()
        framework = ActiveInferenceFramework(model)

        # Test different policies (sequences of actions)
        policies = [np.array([0, 0]), np.array([0, 1])]  # One uniform, one mixed
        posterior = np.array([0.5, 0.5])

        efe_scores = []
        for policy in policies:
            efe_total, _ = framework.calculate_expected_free_energy(posterior, policy)
            efe_scores.append(efe_total)

        # Policies should have different EFE scores
        assert len(set(efe_scores)) > 1  # Not all identical


class TestNumericalStability:
    """Test numerical stability of Active Inference calculations."""

    def test_stability_under_perturbation(self):
        """Test stability under small perturbations."""
        model = create_simple_generative_model()
        framework1 = ActiveInferenceFramework(model)
        framework2 = ActiveInferenceFramework(model)

        # Slightly perturb model parameters
        perturbed_model = {
            'A': model.A.copy(),
            'B': model.B.copy(),
            'C': model.C.copy(),
            'D': model.D.copy()
        }
        perturbed_model['A'] += np.random.normal(0, 0.01, perturbed_model['A'].shape)
        perturbed_model['A'] = np.clip(perturbed_model['A'], 0, 1)

        framework2.generative_model = perturbed_model

        # Test that results are reasonably similar
        posterior = np.array([0.5, 0.5])
        policy = np.array([0])

        efe1, _ = framework1.calculate_expected_free_energy(posterior, policy)
        efe2, _ = framework2.calculate_expected_free_energy(posterior, policy)

        # Results should be reasonably close (within 10%)
        assert abs(efe1 - efe2) / max(abs(efe1), abs(efe2)) < 0.1

    def test_convergence_behavior(self):
        """Test convergence behavior of iterative processes."""
        model = create_simple_generative_model()
        framework = ActiveInferenceFramework(model, precision=0.1)

        # Test multiple iterations of perception
        observations = np.array([0.8, 0.2])

        posteriors = []
        for _ in range(5):
            posterior = framework.perception_as_inference(observations)
            posteriors.append(posterior)

        # Check that posteriors stabilize (similar final values)
        final_posteriors = np.array(posteriors[-3:])
        std_final = np.std(final_posteriors, axis=0)

        # Standard deviation should be small (converged)
        assert np.all(std_final < 0.05)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_state_model(self):
        """Test with single-state model."""
        single_state_model = {
            'A': np.array([[1.0]]),  # 1x1 observation matrix
            'B': np.array([[[1.0]]]),  # 1x1x1 transition matrix
            'C': np.array([0.0]),  # Single observation preference
            'D': np.array([1.0])   # Single state prior
        }

        framework = ActiveInferenceFramework(single_state_model)

        posterior = np.array([1.0])
        policy = np.array([0])

        efe_total, _ = framework.calculate_expected_free_energy(posterior, policy)
        assert isinstance(efe_total, (int, float))

    def test_extreme_probabilities(self):
        """Test with extreme probability values."""
        model = create_simple_generative_model()
        framework = ActiveInferenceFramework(model)

        # Test with very confident posterior
        confident_posterior = np.array([0.99, 0.01])
        policy = np.array([0])

        efe_total, _ = framework.calculate_expected_free_energy(confident_posterior, policy)
        assert np.isfinite(efe_total)

        # Test with uniform posterior
        uniform_posterior = np.array([0.5, 0.5])
        efe_total2, _ = framework.calculate_expected_free_energy(uniform_posterior, policy)
        assert np.isfinite(efe_total2)

    def test_empty_policy(self):
        """Test with empty policy (should handle gracefully)."""
        model = create_simple_generative_model()
        framework = ActiveInferenceFramework(model)

        posterior = np.array([0.5, 0.5])
        empty_policy = np.array([])

        # Should handle empty policy appropriately
        with pytest.raises(ValidationError):
            framework.calculate_expected_free_energy(posterior, empty_policy)