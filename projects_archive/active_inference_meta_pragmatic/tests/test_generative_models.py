"""Tests for Generative Models Implementation.

Comprehensive tests for generative model concepts including A, B, C, D matrices,
inference, prediction, and modeler specifications.
"""

import numpy as np
import pytest
from src.generative_models import (GenerativeModel,
                                   create_simple_generative_model,
                                   demonstrate_generative_model_concepts)
from src.validation import ValidationFramework


class TestGenerativeModel:
    """Test Generative Model core functionality."""

    @pytest.fixture
    def simple_model(self):
        """Create a simple generative model for testing."""
        return create_simple_generative_model()

    def test_initialization(self, simple_model):
        """Test model initialization."""
        assert simple_model.A.shape == (2, 2)  # 2 observations × 2 states
        assert simple_model.B.shape == (2, 2, 2)  # 2 states × 2 states × 2 actions
        assert simple_model.C.shape == (2,)  # 2 observations
        assert simple_model.D.shape == (2,)  # 2 states

        assert simple_model.n_states == 2
        assert simple_model.n_observations == 2
        assert simple_model.n_actions == 2

    def test_matrix_validation(self):
        """Test matrix validation during initialization."""
        # Valid matrices
        A = np.array([[0.8, 0.2], [0.2, 0.8]])
        # B: Two transition matrices (2 states x 2 states x 2 actions)
        # Action 0: stay in current state, Action 1: switch states
        B = np.zeros((2, 2, 2))
        B[:, :, 0] = np.eye(2)  # Stay action
        B[:, :, 1] = np.fliplr(np.eye(2))  # Switch action
        C = np.array([1.0, -1.0])
        D = np.array([0.5, 0.5])

        model = GenerativeModel(A, B, C, D)
        assert model is not None

        # Invalid A matrix (wrong dimensions)
        with pytest.raises(Exception):
            GenerativeModel(np.array([[0.8]]), B, C, D)

        # Invalid D matrix (doesn't sum to 1)
        with pytest.raises(Exception):
            GenerativeModel(A, B, C, np.array([0.3, 0.3]))

    def test_observation_prediction(self, simple_model):
        """Test observation prediction from states."""
        # Predict observation from state 0
        pred_obs_0 = simple_model.predict_observations(0)
        assert len(pred_obs_0) == simple_model.n_observations
        assert np.all(pred_obs_0 >= 0)
        assert np.isclose(np.sum(pred_obs_0), 1.0)

        # Predict observation from state distribution
        state_dist = np.array([0.7, 0.3])
        pred_obs_dist = simple_model.predict_observations(state_dist)
        assert len(pred_obs_dist) == simple_model.n_observations
        assert np.all(pred_obs_dist >= 0)
        assert np.isclose(np.sum(pred_obs_dist), 1.0)

    def test_state_transition_prediction(self, simple_model):
        """Test state transition prediction."""
        # Predict transition from state 0 with action 0
        next_state_0_0 = simple_model.predict_state_transition(0, 0)
        assert len(next_state_0_0) == simple_model.n_states
        assert np.all(next_state_0_0 >= 0)
        assert np.isclose(np.sum(next_state_0_0), 1.0)

        # Predict transition from state distribution with action 1
        state_dist = np.array([0.6, 0.4])
        next_state_dist = simple_model.predict_state_transition(state_dist, 1)
        assert len(next_state_dist) == simple_model.n_states
        assert np.all(next_state_dist >= 0)
        assert np.isclose(np.sum(next_state_dist), 1.0)

    def test_preference_calculation(self, simple_model):
        """Test preference likelihood calculation."""
        # Test single observation preference
        pref_0 = simple_model.calculate_preference_likelihood(0)
        pref_1 = simple_model.calculate_preference_likelihood(1)

        # Preferences should be positive (exp(C))
        assert pref_0 > 0
        assert pref_1 > 0

        # Test observation distribution preference
        obs_dist = np.array([0.8, 0.2])
        pref_dist = simple_model.calculate_preference_likelihood(obs_dist)
        assert pref_dist > 0

    def test_inference(self, simple_model):
        """Test inference from observations."""
        observation = np.array([0.9, 0.1])  # Strong evidence for observation 0

        posterior = simple_model.perform_inference(observation)
        assert len(posterior) == simple_model.n_states
        assert np.all(posterior >= 0)
        assert np.isclose(np.sum(posterior), 1.0)

        # Should favor state that generates observation 0
        assert posterior[0] > posterior[1]  # State 0 more likely

    def test_inference_with_prior(self, simple_model):
        """Test inference with custom prior."""
        observation = np.array([0.5, 0.5])  # Ambiguous observation
        prior = np.array([0.9, 0.1])  # Strong prior for state 0

        posterior = simple_model.perform_inference(observation, prior)
        assert len(posterior) == simple_model.n_states
        assert posterior[0] > prior[0]  # Should strengthen prior belief


class TestGenerativeModelConcepts:
    """Test generative model conceptual demonstrations."""

    def test_create_simple_model(self):
        """Test simple model creation."""
        model = create_simple_generative_model()

        assert isinstance(model, GenerativeModel)
        assert model.n_states == 2
        assert model.n_observations == 2
        assert model.n_actions == 2

    def test_demonstrate_concepts(self):
        """Test generative model concepts demonstration."""
        demonstration = demonstrate_generative_model_concepts()

        required_keys = [
            "model_structure",
            "inference_demo",
            "prediction_demo",
            "transition_demo",
            "preference_demo",
            "modeler_specifications",
            "key_insights",
        ]

        for key in required_keys:
            assert key in demonstration

        # Check model structure
        structure = demonstration["model_structure"]
        assert "n_states" in structure
        assert "n_observations" in structure
        assert "n_actions" in structure

        # Check demonstrations have proper results
        assert "posterior_beliefs" in demonstration["inference_demo"]
        assert "predicted_observations" in demonstration["prediction_demo"]

    def test_modeler_specifications(self):
        """Test modeler specification demonstrations."""
        demonstration = demonstrate_generative_model_concepts()
        specifications = demonstration["modeler_specifications"]

        required_aspects = [
            "epistemic_specification",
            "pragmatic_specification",
            "dynamic_specification",
            "meta_level_implications",
        ]

        for aspect in required_aspects:
            assert aspect in specifications


class TestModelerSpecifications:
    """Test modeler specification functionality."""

    @pytest.fixture
    def model(self):
        """Create test model."""
        return create_simple_generative_model()

    def test_epistemic_specification(self, model):
        """Test epistemic framework specification."""
        specifications = model.demonstrate_modeler_specifications()

        epistemic = specifications["epistemic_specification"]
        assert "generative_model_design" in epistemic
        assert "matrix_A_role" in epistemic
        assert "matrix_D_role" in epistemic

    def test_pragmatic_specification(self, model):
        """Test pragmatic framework specification."""
        specifications = model.demonstrate_modeler_specifications()

        pragmatic = specifications["pragmatic_specification"]
        assert "matrix_C_role" in pragmatic
        assert "pragmatic_framework" in pragmatic

    def test_dynamic_specification(self, model):
        """Test dynamic specification through B matrix."""
        specifications = model.demonstrate_modeler_specifications()

        dynamic = specifications["dynamic_specification"]
        assert "matrix_B_role" in dynamic
        assert "agency_framework" in dynamic

    def test_meta_level_implications(self, model):
        """Test meta-level implications of specifications."""
        specifications = model.demonstrate_modeler_specifications()

        meta_implications = specifications["meta_level_implications"]
        assert "epistemic_meta" in meta_implications
        assert "pragmatic_meta" in meta_implications


class TestGenerativeModelValidation:
    """Test generative model validation."""

    @pytest.fixture
    def validator(self):
        """Create validation framework instance."""
        return ValidationFramework()

    def test_model_validation(self, validator):
        """Test generative model structure validation."""
        model = create_simple_generative_model()

        # Test valid model
        model_dict = {"A": model.A, "B": model.B, "C": model.C, "D": model.D}
        validation_result = validator.validate_generative_model(model_dict)
        assert validation_result["valid"] is True
        assert "model_structure" in validation_result
        assert "compatibility_checks" in validation_result

        # Test invalid model (wrong dimensions)
        invalid_model = {
            "A": np.array([[0.8, 0.2]]),  # Wrong shape
            "B": np.array([[[0.9, 0.1], [0.1, 0.9]]]),
            "C": np.array([1.0, -1.0]),
            "D": np.array([0.5, 0.5]),
        }

        with pytest.raises(Exception):
            validator.validate_generative_model(invalid_model)

    def test_probability_distribution_validation(self, validator):
        """Test probability distribution validation in model."""
        model = create_simple_generative_model()

        # Test observation likelihoods (columns of A should be distributions)
        for state in range(model.n_states):
            obs_likelihood = model.A[:, state]
            result = validator.validate_probability_distribution(obs_likelihood)
            assert result["valid"] is True

        # Test prior beliefs (D)
        result = validator.validate_probability_distribution(model.D)
        assert result["valid"] is True


class TestGenerativeModelMathematics:
    """Test mathematical properties of generative models."""

    def test_matrix_properties(self):
        """Test mathematical properties of model matrices."""
        model = create_simple_generative_model()

        # A matrix: each column should be a valid probability distribution
        for state in range(model.n_states):
            col = model.A[:, state]
            assert np.all(col >= 0)
            assert np.isclose(np.sum(col), 1.0)

        # B matrix: each action's transition matrix should be stochastic
        for action in range(model.n_actions):
            transition_matrix = model.B[:, :, action]
            for from_state in range(model.n_states):
                row = transition_matrix[:, from_state]
                assert np.all(row >= 0)
                assert np.isclose(np.sum(row), 1.0)

    def test_inference_consistency(self):
        """Test inference consistency properties."""
        model = create_simple_generative_model()

        # Test that inference preserves information
        observation = np.array([0.8, 0.2])

        posterior = model.perform_inference(observation)

        # Posterior should be a valid distribution
        assert np.all(posterior >= 0)
        assert np.isclose(np.sum(posterior), 1.0)

        # For this simple model, posterior should reflect observation likelihood
        # State 0 is more likely to generate observation 0
        assert posterior[0] > posterior[1]

    def test_prediction_consistency(self):
        """Test prediction consistency."""
        model = create_simple_generative_model()

        # Predict from known state
        pred_obs = model.predict_observations(0)

        # Should match the corresponding column of A
        expected = model.A[:, 0]
        assert np.allclose(pred_obs, expected)

    def test_preference_mathematics(self):
        """Test preference calculation mathematics."""
        model = create_simple_generative_model()

        # Preferences should be exp(C)
        expected_pref_0 = np.exp(model.C[0])
        expected_pref_1 = np.exp(model.C[1])

        actual_pref_0 = model.calculate_preference_likelihood(0)
        actual_pref_1 = model.calculate_preference_likelihood(1)

        assert np.isclose(actual_pref_0, expected_pref_0)
        assert np.isclose(actual_pref_1, expected_pref_1)


class TestGenerativeModelIntegration:
    """Test generative model integration with other components."""

    def test_with_active_inference(self):
        """Test generative model integration with Active Inference."""
        from src.active_inference import ActiveInferenceFramework

        model = create_simple_generative_model()
        ai_framework = ActiveInferenceFramework(model)

        # Should work together seamlessly
        observation = np.array([0.7, 0.3])
        posterior = ai_framework.perception_as_inference(observation)

        assert len(posterior) == model.n_states
        assert np.all(posterior >= 0)
        assert np.isclose(np.sum(posterior), 1.0)

    def test_model_scalability(self):
        """Test model scalability with different sizes."""
        # Test larger model
        n_states = 3
        n_observations = 4
        n_actions = 2

        # Create larger matrices
        A = np.random.rand(n_observations, n_states)
        A = A / A.sum(axis=0, keepdims=True)  # Normalize columns

        B = np.random.rand(n_states, n_states, n_actions)
        for action in range(n_actions):
            B[:, :, action] = B[:, :, action] / B[:, :, action].sum(
                axis=0, keepdims=True
            )

        C = np.random.randn(n_observations)
        D = np.random.rand(n_states)
        D = D / D.sum()

        large_model = GenerativeModel(A, B, C, D)

        assert large_model.n_states == n_states
        assert large_model.n_observations == n_observations
        assert large_model.n_actions == n_actions

        # Test operations on larger model
        observation = np.zeros(n_observations)
        observation[0] = 1.0

        posterior = large_model.perform_inference(observation)
        assert len(posterior) == n_states
        assert np.all(posterior >= 0)
        assert np.isclose(np.sum(posterior), 1.0)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_deterministic_model(self):
        """Test with deterministic model (no uncertainty)."""
        # Perfect observation likelihoods
        A = np.array([[1.0, 0.0], [0.0, 1.0]])
        # B: Identity transitions for both actions (deterministic)
        B = np.zeros((2, 2, 2))
        B[:, :, 0] = np.eye(2)  # Stay action (deterministic)
        B[:, :, 1] = np.eye(2)  # Also stay action (deterministic)
        C = np.array([0.0, 0.0])  # Neutral preferences
        D = np.array([0.5, 0.5])

        det_model = GenerativeModel(A, B, C, D)

        # Inference should be perfect
        observation = np.array([1.0, 0.0])  # Definitely observation 0
        posterior = det_model.perform_inference(observation)

        # Should infer state 0 with near certainty (allow floating point precision)
        np.testing.assert_allclose(posterior[0], 1.0, atol=1e-6)
        np.testing.assert_allclose(posterior[1], 0.0, atol=1e-6)

    def test_extreme_preferences(self):
        """Test with extreme preference values."""
        model = create_simple_generative_model()

        # Modify C to have extreme values
        model.C = np.array([10.0, -10.0])  # Very strong preferences

        # Preferences should still be calculable
        pref_0 = model.calculate_preference_likelihood(0)
        pref_1 = model.calculate_preference_likelihood(1)

        assert np.isfinite(pref_0)
        assert np.isfinite(pref_1)
        assert pref_0 > pref_1  # Should reflect preference ordering

    def test_uniform_matrices(self):
        """Test with uniform (uninformative) matrices."""
        n_states = 2
        n_observations = 2
        n_actions = 2

        # Uniform matrices
        A = np.full((n_observations, n_states), 0.5)
        B = np.full((n_states, n_states, n_actions), 0.5)
        C = np.zeros(n_observations)
        D = np.full(n_states, 0.5)

        uniform_model = GenerativeModel(A, B, C, D)

        # Inference should return prior (uniform)
        observation = np.array([0.5, 0.5])
        posterior = uniform_model.perform_inference(observation)

        assert np.allclose(posterior, D)  # Should return prior
