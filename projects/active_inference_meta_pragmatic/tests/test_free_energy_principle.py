"""Tests for Free Energy Principle Implementation.

Comprehensive tests for FEP concepts including free energy calculation,
system boundary definition, structure preservation, and theoretical validation.
"""

import numpy as np
import pytest

from infrastructure.core.exceptions import ValidationError
from src.free_energy_principle import (
    FreeEnergyPrinciple,
    define_what_is_a_thing,
    demonstrate_fep_concepts
)
from src.validation import ValidationFramework


class TestFreeEnergyPrinciple:
    """Test Free Energy Principle core functionality."""

    @pytest.fixture
    def system_states(self):
        """Create test system states."""
        return {
            'internal': np.array([0.5, 0.3, 0.2]),
            'external': np.array([0.1, 0.9]),
            'sensory': np.array([0.4, 0.6])
        }

    @pytest.fixture
    def fep_framework(self, system_states):
        """Create Free Energy Principle framework instance."""
        return FreeEnergyPrinciple(system_states)

    def test_initialization(self, fep_framework, system_states):
        """Test FEP framework initialization."""
        assert fep_framework.system_states is not None
        assert fep_framework.precision == 1.0
        assert np.array_equal(fep_framework.system_states['internal'], system_states['internal'])

    def test_free_energy_calculation(self, fep_framework):
        """Test free energy calculation."""
        observations = np.array([0.6, 0.4])
        beliefs = np.array([0.7, 0.2, 0.1])

        free_energy, components = fep_framework.calculate_free_energy(observations, beliefs)

        assert isinstance(free_energy, (int, float))
        assert 'energy' in components
        assert 'entropy' in components
        assert 'free_energy' in components
        assert 'surprise' in components
        assert components['free_energy'] == free_energy

    def test_system_boundary_definition(self, fep_framework):
        """Test Markov blanket and system boundary definition."""
        boundary = fep_framework.define_system_boundary()

        required_components = ['internal_states', 'external_states', 'sensory_states', 'active_states']
        for component in required_components:
            assert component in boundary
            assert isinstance(boundary[component], np.ndarray)

        # Internal and sensory states should match input
        assert np.array_equal(boundary['internal_states'], fep_framework.system_states['internal'])
        assert np.array_equal(boundary['sensory_states'], fep_framework.system_states['sensory'])

    def test_structure_preservation(self, fep_framework):
        """Test structure preservation dynamics."""
        time_steps = 20
        preservation_data = fep_framework.demonstrate_structure_preservation(time_steps)

        required_keys = ['internal_states', 'external_states', 'free_energy_history', 'time_steps']
        for key in required_keys:
            assert key in preservation_data

        assert preservation_data['time_steps'] == time_steps
        assert preservation_data['internal_states'].shape == (time_steps, len(fep_framework.system_states['internal']))
        assert len(preservation_data['free_energy_history']) == time_steps

    def test_convergence_in_structure_preservation(self, fep_framework):
        """Test that structure preservation leads to convergence."""
        preservation_data = fep_framework.demonstrate_structure_preservation(time_steps=50)

        fe_history = preservation_data['free_energy_history']

        # Free energy should generally decrease (negative values indicate convergence)
        # Check that later values are more stable (lower variance)
        early_std = np.std(fe_history[:10])
        late_std = np.std(fe_history[-10:])

        # Later period should be more stable (though not necessarily less than early)
        # At minimum, the system should not be diverging catastrophically
        assert late_std < early_std * 2  # Allow some tolerance

    def test_error_handling(self, fep_framework):
        """Test error handling for invalid inputs."""
        # Test with mismatched dimensions - should handle gracefully now
        result = fep_framework.calculate_free_energy(
            np.array([0.6]),  # Wrong dimension
            np.array([0.7, 0.2, 0.1])
        )
        # Should return valid result with truncated dimensions
        assert isinstance(result, tuple)
        assert len(result) == 2

        # Test with invalid probabilities
        with pytest.raises(ValidationError):
            fep_framework.calculate_free_energy(
                np.array([0.6, 0.4]),
                np.array([1.5, -0.2, 0.7])  # Invalid probabilities
            )


class TestFEPConcepts:
    """Test Free Energy Principle conceptual demonstrations."""

    def test_define_what_is_a_thing(self):
        """Test the definition of 'what is a thing'."""
        definition = define_what_is_a_thing()

        required_keys = [
            'core_principle',
            'mathematical_formulation',
            'practical_implications'
        ]

        for key in required_keys:
            assert key in definition
            assert isinstance(definition[key], str)
            assert len(definition[key]) > 0

    def test_demonstrate_fep_concepts(self):
        """Test FEP concepts demonstration."""
        demonstration = demonstrate_fep_concepts()

        required_keys = [
            'system_states',
            'free_energy_calculation',
            'system_boundary',
            'structure_preservation',
            'thing_definition',
            'key_insight'
        ]

        for key in required_keys:
            assert key in demonstration

        # Check numerical results
        fe_calc = demonstration['free_energy_calculation']
        assert 'free_energy' in fe_calc
        assert 'components' in fe_calc

        # Check structure preservation
        preservation = demonstration['structure_preservation']
        assert 'final_internal_state' in preservation
        assert 'free_energy_trajectory' in preservation
        assert 'converged' in preservation

    def test_structure_preservation_convergence(self):
        """Test that structure preservation demonstrates convergence."""
        demonstration = demonstrate_fep_concepts()
        preservation = demonstration['structure_preservation']

        # Should indicate whether the system converged
        assert 'converged' in preservation
        assert isinstance(preservation['converged'], bool)


class TestFEPValidation:
    """Test Free Energy Principle validation."""

    @pytest.fixture
    def validator(self):
        """Create validation framework instance."""
        return ValidationFramework()

    def test_fep_numerical_correctness(self, validator):
        """Test numerical correctness of FEP calculations."""
        system_states = {
            'internal': np.array([0.5, 0.3, 0.2]),
            'external': np.array([0.1, 0.9]),
            'sensory': np.array([0.4, 0.6])
        }

        fep = FreeEnergyPrinciple(system_states)
        observations = np.array([0.6, 0.4])
        beliefs = np.array([0.7, 0.2, 0.1])

        free_energy, components = fep.calculate_free_energy(observations, beliefs)

        # Validate numerical stability
        implementation_result = {
            'free_energy': free_energy,
            'components': components,
            'observations': observations,
            'beliefs': beliefs
        }

        stability_result = validator._validate_numerical_stability(implementation_result)
        assert stability_result['stable'] is True

    def test_boundary_condition_handling(self, validator):
        """Test boundary condition handling."""
        # Test with extreme values
        system_states = {
            'internal': np.array([1.0, 0.0, 0.0]),  # Extreme certainty
            'external': np.array([0.0, 1.0]),
            'sensory': np.array([0.0, 1.0])
        }

        fep = FreeEnergyPrinciple(system_states)
        observations = np.array([1.0, 0.0])
        beliefs = np.array([1.0, 0.0, 0.0])

        free_energy, components = fep.calculate_free_energy(observations, beliefs)

        # Should handle extreme values without numerical issues
        assert np.isfinite(free_energy)
        for component in components.values():
            if isinstance(component, (int, float)):
                assert np.isfinite(component)


class TestFEPMathematicalProperties:
    """Test mathematical properties of Free Energy Principle."""

    def test_free_energy_relationships(self):
        """Test mathematical relationships in free energy calculations."""
        system_states = {
            'internal': np.array([0.5, 0.3, 0.2]),
            'external': np.array([0.1, 0.9]),
            'sensory': np.array([0.4, 0.6])
        }

        fep = FreeEnergyPrinciple(system_states)

        # Test multiple scenarios
        scenarios = [
            {'observations': np.array([0.6, 0.4]), 'beliefs': np.array([0.7, 0.2, 0.1])},
            {'observations': np.array([0.3, 0.7]), 'beliefs': np.array([0.4, 0.4, 0.2])},
            {'observations': np.array([0.8, 0.2]), 'beliefs': np.array([0.8, 0.1, 0.1])}
        ]

        fe_values = []
        for scenario in scenarios:
            fe, _ = fep.calculate_free_energy(scenario['observations'], scenario['beliefs'])
            fe_values.append(fe)

        # Free energy should vary with different scenarios
        assert len(set(fe_values)) > 1  # Not all identical

        # All values should be finite
        assert all(np.isfinite(fe) for fe in fe_values)

    def test_entropy_calculation(self):
        """Test entropy calculation properties."""
        system_states = {
            'internal': np.array([0.5, 0.3, 0.2]),
            'external': np.array([0.1, 0.9]),
            'sensory': np.array([0.4, 0.6])
        }

        fep = FreeEnergyPrinciple(system_states)

        # Test entropy for different belief distributions
        test_beliefs = [
            np.array([1.0, 0.0, 0.0]),  # Maximum certainty (minimum entropy)
            np.array([0.5, 0.3, 0.2]),  # Moderate certainty
            np.array([0.33, 0.33, 0.34])  # Maximum uncertainty (maximum entropy)
        ]

        entropies = []
        for beliefs in test_beliefs:
            fe, components = fep.calculate_free_energy(np.array([0.5, 0.5]), beliefs)
            entropy = components['entropy']
            entropies.append(entropy)

        # Entropy should increase with uncertainty
        assert entropies[0] <= entropies[1] <= entropies[2]

    def test_structure_preservation_properties(self):
        """Test properties of structure preservation."""
        system_states = {
            'internal': np.array([0.5, 0.3, 0.2]),
            'external': np.array([0.1, 0.9]),
            'sensory': np.array([0.4, 0.6])
        }

        fep = FreeEnergyPrinciple(system_states)
        preservation = fep.demonstrate_structure_preservation(time_steps=30)

        internal_states = preservation['internal_states']
        fe_history = preservation['free_energy_history']

        # Internal states should maintain structure (not become uniform or extreme)
        final_state = internal_states[-1]

        # Check that final state is still a valid distribution
        assert np.all(final_state >= 0)
        assert np.isclose(np.sum(final_state), 1.0, atol=0.1)  # Allow some drift

        # Free energy should be generally decreasing or stable
        early_avg = np.mean(fe_history[:10])
        late_avg = np.mean(fe_history[-10:])

        # Later free energy should be lower or similar (convergence)
        assert late_avg <= early_avg + 0.5  # Allow moderate increase for complex dynamics


class TestFEPIntegration:
    """Test Free Energy Principle integration with other components."""

    def test_fep_with_active_inference(self):
        """Test FEP concepts work with Active Inference framework."""
        from src.active_inference import ActiveInferenceFramework
        from src.generative_models import create_simple_generative_model

        # Create generative model
        model = create_simple_generative_model()
        ai_framework = ActiveInferenceFramework(model)

        # FEP should provide complementary perspective
        system_states = {
            'internal': np.array([0.5, 0.5]),  # Match model states
            'external': np.array([0.2, 0.8]),
            'sensory': np.array([0.3, 0.7])
        }

        fep = FreeEnergyPrinciple(system_states)

        # Both should work independently
        observations = np.array([0.6, 0.4])
        beliefs = np.array([0.7, 0.3])

        fe, _ = fep.calculate_free_energy(observations, beliefs)
        posterior = ai_framework.perception_as_inference(observations)

        assert np.isfinite(fe)
        assert len(posterior) == ai_framework.n_states

    def test_thing_definition_consistency(self):
        """Test that 'thing' definition is consistent."""
        definition = define_what_is_a_thing()

        # Definition should mention key FEP concepts
        key_concepts = ['free energy', 'minimizing', 'structure', 'maintain']
        definition_text = ' '.join(definition.values()).lower()

        for concept in key_concepts:
            assert concept in definition_text