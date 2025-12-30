"""Free Energy Principle Implementation.

This module implements concepts from the Free Energy Principle (FEP), which provides
a unifying framework for understanding what constitutes a "thing" in the context
of Active Inference. The FEP posits that any system that maintains its structure
over time can be understood as minimizing free energy.

Key Concepts:
- Free Energy: Upper bound on surprise (negative log evidence)
- Variational Free Energy: Tractable approximation to free energy
- System Boundaries: Markov blankets separating internal and external states
- Structure Preservation: Systems maintain their organization over time
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from numpy.typing import NDArray

from infrastructure.core.exceptions import ValidationError
from infrastructure.core.logging_utils import get_logger

logger = get_logger(__name__)


class FreeEnergyPrinciple:
    """Implementation of Free Energy Principle concepts.

    The Free Energy Principle provides a mathematical framework for understanding
    self-organizing systems that maintain their structure over time.
    """

    def __init__(self, system_states: Dict[str, NDArray], precision: float = 1.0) -> None:
        """Initialize Free Energy Principle framework.

        Args:
            system_states: Dictionary containing internal, external, and sensory states
            precision: Precision parameter for free energy calculations
        """
        # Ensure all system states have compatible shapes
        state_shapes = [arr.shape[0] for arr in system_states.values()]
        state_shape_set = set(state_shapes)

        if len(state_shape_set) > 1:
            # Make all states have the same first dimension (state space size)
            max_shape = max(state_shape_set)
            corrected_states = {}

            for key, arr in system_states.items():
                current_shape = arr.shape[0]
                if current_shape < max_shape:
                    # Pad with zeros to match max shape - more efficient than creating zeros then copying
                    padded = np.zeros(max_shape, dtype=arr.dtype)
                    padded[:current_shape] = arr
                    corrected_states[key] = padded
                else:
                    corrected_states[key] = arr

            self.system_states = corrected_states
            logger.debug(f"Normalized {len(corrected_states)} system states to shape {max_shape}")
        else:
            self.system_states = system_states

        self.precision = precision
        self._validate_system_states()

        logger.info(f"Initialized Free Energy Principle framework with precision {precision}")

    def _validate_system_states(self) -> None:
        """Validate system state structure.

        Raises:
            ValidationError: If required states are missing or have incompatible shapes
        """
        required_states = ['internal', 'external', 'sensory']
        for state_name in required_states:
            if state_name not in self.system_states:
                raise ValidationError(f"Missing required system state: {state_name}")

        # Validate shapes for compatibility
        internal_shape = self.system_states['internal'].shape
        sensory_shape = self.system_states['sensory'].shape
        if internal_shape != sensory_shape:
            logger.warning(
                f"Internal state shape {internal_shape} differs from sensory state shape {sensory_shape}. "
                "This may affect free energy calculations."
            )

    def calculate_free_energy(self, observations: NDArray, beliefs: NDArray) -> Tuple[float, Dict[str, float]]:
        """Calculate variational free energy.

        Free Energy = Energy - Entropy = Surprise - Information Gain

        Args:
            observations: Current sensory observations
            beliefs: Current belief distribution over hidden states

        Returns:
            Tuple of (free_energy, components) where components contains:
            - 'energy': Expected energy term
            - 'entropy': Entropy term
            - 'surprise': Surprise component
        """
        try:
            # Energy term: expected log likelihood
            energy = self._calculate_energy(observations, beliefs)

            # Entropy term: KL divergence between posterior and prior
            entropy = self._calculate_entropy(beliefs)

            # Total variational free energy
            free_energy = energy - entropy

            # Surprise component (negative log evidence)
            surprise = self._calculate_surprise(observations)

            components = {
                'energy': energy,
                'entropy': entropy,
                'free_energy': free_energy,
                'surprise': surprise
            }

            logger.debug(f"Free energy calculation: F={free_energy:.4f}, E={energy:.4f}, H={entropy:.4f}")
            return free_energy, components

        except Exception as e:
            logger.error(f"Error calculating free energy: {e}")
            raise ValidationError(f"Free energy calculation failed: {e}") from e

    def _calculate_energy(self, observations: NDArray, beliefs: NDArray) -> float:
        """Calculate energy term (expected log likelihood)."""
        # Simplified energy calculation
        # In full implementation, this would involve generative model likelihoods

        # Validate probability values
        if np.any(observations < 0) or np.any(observations > 1):
            raise ValidationError("Observations must be valid probabilities (0 ≤ p ≤ 1)")

        if np.any(beliefs < 0) or np.any(beliefs > 1):
            raise ValidationError("Beliefs must be valid probabilities (0 ≤ p ≤ 1)")

        # Ensure observations and beliefs have compatible shapes for calculation
        if observations.shape != beliefs.shape:
            # Handle different dimensionalities in simplified implementation
            # Assume observations represent likelihoods over observation space
            # and beliefs represent posterior over hidden states
            # For simplified case, take dot product if dimensions allow
            try:
                if len(observations.shape) == 1 and len(beliefs.shape) == 1:
                    # If both 1D, assume observations are likelihoods for each belief state
                    # Take the smaller dimension and use element-wise or truncate
                    min_len = min(len(observations), len(beliefs))
                    observations = observations[:min_len]
                    beliefs = beliefs[:min_len]
                else:
                    # Try matrix multiplication if shapes allow
                    result = observations @ beliefs
                    if np.isscalar(result):
                        return -result
                    else:
                        return -np.sum(result)
            except Exception as broadcast_error:
                raise ValidationError(
                    f"Cannot compute energy from observations (shape {observations.shape}) "
                    f"and beliefs (shape {beliefs.shape}): {broadcast_error}"
                ) from broadcast_error

        return -np.sum(observations * np.log(np.clip(beliefs, 1e-10, 1.0)))

    def _calculate_entropy(self, beliefs: NDArray) -> float:
        """Calculate entropy of belief distribution."""
        beliefs = np.clip(beliefs, 1e-10, 1.0)
        return -np.sum(beliefs * np.log(beliefs))

    def _calculate_surprise(self, observations: NDArray) -> float:
        """Calculate surprise (negative log evidence)."""
        # Simplified surprise calculation
        return -np.sum(observations * np.log(np.clip(observations, 1e-10, 1.0)))

    def define_system_boundary(self) -> Dict[str, NDArray]:
        """Define Markov blanket (system boundary).

        The Markov blanket separates internal states from external states,
        with sensory and active states forming the boundary.

        Returns:
            Dictionary containing boundary state definitions
        """
        try:
            boundary = {
                'internal_states': self.system_states['internal'],
                'external_states': self.system_states['external'],
                'sensory_states': self.system_states['sensory'],
                'active_states': self._calculate_active_states()
            }

            logger.info("Defined system boundary with Markov blanket")
            return boundary

        except Exception as e:
            logger.error(f"Error defining system boundary: {e}")
            raise ValidationError(f"System boundary definition failed: {e}") from e

    def _calculate_active_states(self) -> NDArray:
        """Calculate active states from internal and sensory states."""
        # Active states represent the system's influence on the world
        internal = self.system_states['internal']
        sensory = self.system_states['sensory']

        # Simplified calculation - in practice would involve action policies
        return np.tanh(internal + sensory)

    def demonstrate_structure_preservation(self, time_steps: int = 100) -> Dict[str, NDArray]:
        """Demonstrate structure preservation over time.

        Systems maintain their organization by minimizing free energy,
        preserving structural integrity over time.

        Args:
            time_steps: Number of time steps to simulate

        Returns:
            Dictionary containing time series of system states and free energy
        """
        try:
            # Initialize system state
            internal_state = self.system_states['internal'].copy()
            external_state = self.system_states['external'].copy()

            # Track evolution over time
            internal_history = []
            external_history = []
            free_energy_history = []

            for t in range(time_steps):
                # Generate observations from current state
                observations = self._generate_observations(internal_state, external_state)

                # Update beliefs through variational inference
                beliefs = self._variational_inference(observations)

                # Calculate free energy
                free_energy, _ = self.calculate_free_energy(observations, beliefs)
                free_energy_history.append(free_energy)

                # Update internal state (structure preservation)
                internal_state = self._update_internal_state(internal_state, beliefs)

                # Update external state (environmental dynamics)
                external_state = self._update_external_state(external_state)

                # Store history
                internal_history.append(internal_state.copy())
                external_history.append(external_state.copy())

            result = {
                'internal_states': np.array(internal_history),
                'external_states': np.array(external_history),
                'free_energy_history': np.array(free_energy_history),
                'time_steps': time_steps
            }

            logger.info(f"Demonstrated structure preservation over {time_steps} time steps")
            return result

        except Exception as e:
            logger.error(f"Error demonstrating structure preservation: {e}")
            raise ValidationError(f"Structure preservation demonstration failed: {e}") from e

    def _generate_observations(self, internal: NDArray, external: NDArray) -> NDArray:
        """Generate sensory observations from system states."""
        # Ensure arrays are compatible for addition
        min_len = min(len(internal), len(external))
        internal_trunc = internal[:min_len] if len(internal) > min_len else internal
        external_trunc = external[:min_len] if len(external) > min_len else external

        # Simplified observation generation
        return np.clip(internal_trunc + external_trunc + np.random.normal(0, 0.1, min_len), 0, 1)

    def _variational_inference(self, observations: NDArray) -> NDArray:
        """Perform variational inference to update beliefs."""
        # Simplified inference - in practice would involve optimization
        n_obs = len(observations)  # Match observations shape
        beliefs = np.ones(n_obs) / n_obs
        return beliefs

    def _update_internal_state(self, internal: NDArray, beliefs: NDArray) -> NDArray:
        """Update internal state to minimize free energy."""
        # Structure preservation through homeostatic regulation
        # Handle dimension mismatch by expanding beliefs to match internal state
        if len(beliefs) < len(internal):
            # Pad beliefs with zeros to match internal dimension
            beliefs_expanded = np.pad(beliefs, (0, len(internal) - len(beliefs)), 'constant')
        else:
            # Truncate beliefs to match internal dimension
            beliefs_expanded = beliefs[:len(internal)]

        return internal + 0.1 * (beliefs_expanded - internal)

    def _update_external_state(self, external: NDArray) -> NDArray:
        """Update external state (environmental dynamics)."""
        # Simplified environmental dynamics
        return external + 0.05 * np.random.normal(0, 1, external.shape)


def define_what_is_a_thing() -> Dict[str, str]:
    """Define what constitutes a 'thing' according to the Free Energy Principle.

    Returns:
        Dictionary explaining the FEP definition of a 'thing'
    """
    definition = {
        'core_principle': """
        Any system that maintains its structure over time can be understood as
        minimizing free energy. This provides a unifying framework for understanding
        diverse phenomena under a single theoretical umbrella.
        """,

        'mathematical_formulation': """
        A 'thing' is a system that bounds its states with a Markov blanket,
        separating internal states from external states. The system maintains
        its organization by minimizing variational free energy.
        """,

        'practical_implications': """
        This framework bridges physics and cognition, allowing us to understand
        biological systems, artificial agents, and even social organizations
        as systems that maintain their structural integrity over time.
        """,

        'active_inference_connection': """
        In Active Inference, agents are 'things' that use generative models
        to predict and act upon their environment, maintaining homeostasis
        through free energy minimization.
        """
    }

    return definition


def demonstrate_fep_concepts() -> Dict[str, Union[str, Dict]]:
    """Demonstrate core Free Energy Principle concepts.

    Returns:
        Dictionary containing conceptual demonstrations and examples
    """
    # Define a simple system
    system_states = {
        'internal': np.array([0.5, 0.3, 0.2]),  # Internal state distribution
        'external': np.array([0.1, 0.9]),        # External environment
        'sensory': np.array([0.4, 0.6, 0.0])    # Sensory inputs (match internal dimension)
    }

    fep = FreeEnergyPrinciple(system_states)

    # Demonstrate free energy calculation
    observations = system_states['internal']  # Match internal state dimension
    beliefs = system_states['internal']  # Use internal state as beliefs

    free_energy, components = fep.calculate_free_energy(observations, beliefs)

    # Demonstrate system boundary
    boundary = fep.define_system_boundary()

    # Demonstrate structure preservation
    preservation_demo = fep.demonstrate_structure_preservation(time_steps=20)

    # Define what is a thing
    thing_definition = define_what_is_a_thing()

    demonstration = {
        'system_states': {k: v.tolist() for k, v in system_states.items()},
        'free_energy_calculation': {
            'free_energy': free_energy,
            'components': components
        },
        'system_boundary': {k: v.tolist() for k, v in boundary.items()},
        'structure_preservation': {
            'final_internal_state': preservation_demo['internal_states'][-1].tolist(),
            'free_energy_trajectory': preservation_demo['free_energy_history'].tolist(),
            'converged': bool(np.std(preservation_demo['free_energy_history'][-10:]) < 0.01)
        },
        'thing_definition': thing_definition,
        'key_insight': """
        The Free Energy Principle provides a bridge between physics and cognition,
        showing how diverse systems (biological, artificial, social) maintain their
        organization through free energy minimization. This unifies our understanding
        of 'things' across different domains.
        """
    }

    logger.info("Demonstrated Free Energy Principle concepts with numerical examples")
    return demonstration