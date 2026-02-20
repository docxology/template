"""Generative Models Implementation.

This module implements generative model concepts central to Active Inference.
Generative models encode probabilistic relationships between hidden states,
observations, actions, and preferences through matrices A, B, C, and D.

Key Components:
- A matrix: Observation likelihoods P(o|s) - how hidden states generate observations
- B matrix: Transition probabilities P(s'|s,a) - how actions change states
- C matrix: Preference priors - desired outcomes and avoidance
- D matrix: Prior beliefs P(s) - initial state distribution

The modeler specifies these matrices to define the agent's understanding of its world.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from numpy.typing import NDArray
from ..utils.exceptions import ValidationError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class GenerativeModel:
    """Implementation of Active Inference generative models.

    A generative model consists of four matrices (A, B, C, D) that encode
    the probabilistic relationships defining an agent's understanding of its world.
    """

    def __init__(self, A: NDArray, B: NDArray, C: NDArray, D: NDArray) -> None:
        """Initialize generative model with A, B, C, D matrices.

        Args:
            A: Observation likelihood matrix P(o|s) [n_observations × n_states]
            B: Transition matrix P(s'|s,a) [n_states × n_states × n_actions]
            C: Preference matrix (log priors over observations) [n_observations]
            D: Prior beliefs P(s) [n_states]

        Raises:
            ValidationError: If matrices have incompatible dimensions
        """
        self.A = A  # P(o|s) - observation likelihoods
        self.B = B  # P(s'|s,a) - state transitions
        self.C = C  # Preference priors (log probabilities)
        self.D = D  # Prior beliefs P(s)

        self._validate_matrices()
        self.n_states = D.shape[0]
        self.n_observations = A.shape[0]
        self.n_actions = B.shape[2] if len(B.shape) > 2 else 1

        logger.info(
            f"Initialized generative model: {self.n_states} states, "
            f"{self.n_observations} observations, {self.n_actions} actions"
        )

    def _validate_matrices(self) -> None:
        """Validate matrix dimensions and compatibility.

        Raises:
            ValidationError: If matrices are malformed or incompatible
        """
        # Check basic shapes
        if len(self.A.shape) != 2:
            raise ValidationError("Matrix A must be 2-dimensional")
        if len(self.D.shape) != 1:
            raise ValidationError("Matrix D must be 1-dimensional")
        if len(self.C.shape) != 1:
            raise ValidationError("Matrix C must be 1-dimensional")

        n_states = self.D.shape[0]
        n_observations = self.A.shape[0]

        # Check compatibility
        if self.A.shape[1] != n_states:
            raise ValidationError(
                f"A matrix columns ({self.A.shape[1]}) must match D length ({n_states})"
            )

        if self.C.shape[0] != n_observations:
            raise ValidationError(
                f"C matrix length ({self.C.shape[0]}) must match A rows ({n_observations})"
            )

        if len(self.B.shape) == 3:
            if self.B.shape[0] != n_states or self.B.shape[1] != n_states:
                raise ValidationError(
                    f"B matrix first two dimensions must be ({n_states}, {n_states})"
                )

        # Validate D is a valid probability distribution
        if not np.isclose(np.sum(self.D), 1.0, atol=1e-6):
            raise ValidationError(
                f"D matrix must sum to 1.0 (current sum: {np.sum(self.D):.6f})"
            )

    def predict_observations(self, state: Union[int, NDArray]) -> NDArray:
        """Predict observations given hidden state.

        Args:
            state: Hidden state (index or distribution)

        Returns:
            Predicted observation distribution P(o|s)
        """
        try:
            if isinstance(state, (int, np.integer)):
                # Single state index
                prediction = self.A[:, state]
            else:
                # State distribution - marginalize
                prediction = self.A @ state

            # Ensure proper probability distribution
            prediction = np.clip(prediction, 0, 1)
            if prediction.sum() > 0:
                prediction = prediction / prediction.sum()

            return prediction

        except Exception as e:
            logger.error(f"Error predicting observations: {e}")
            raise ValidationError(f"Observation prediction failed: {e}") from e

    def predict_state_transition(
        self, current_state: Union[int, NDArray], action: int
    ) -> NDArray:
        """Predict state transition given current state and action.

        Args:
            current_state: Current hidden state (index or distribution)
            action: Action index

        Returns:
            Predicted next state distribution P(s'|s,a)
        """
        try:
            if isinstance(current_state, (int, np.integer)):
                # Single state - use transition matrix directly
                transition = self.B[:, current_state, action]
            else:
                # State distribution - matrix multiplication
                transition_matrix = self.B[:, :, action]
                transition = transition_matrix @ current_state

            # Ensure proper probability distribution
            transition = np.clip(transition, 0, 1)
            if transition.sum() > 0:
                transition = transition / transition.sum()

            return transition

        except Exception as e:
            logger.error(f"Error predicting state transition: {e}")
            raise ValidationError(f"State transition prediction failed: {e}") from e

    def calculate_preference_likelihood(
        self, observation: Union[int, NDArray]
    ) -> float:
        """Calculate preference likelihood for observation.

        Args:
            observation: Observation (index or distribution)

        Returns:
            Preference likelihood (exp(C) gives preference strength)
        """
        try:
            if isinstance(observation, (int, np.integer)):
                # Single observation
                preference = np.exp(self.C[observation])
            else:
                # Observation distribution - expected preference
                preference = np.exp(self.C) @ observation

            return float(preference)

        except Exception as e:
            logger.error(f"Error calculating preference likelihood: {e}")
            raise ValidationError(f"Preference calculation failed: {e}") from e

    def perform_inference(
        self, observation: NDArray, prior_beliefs: Optional[NDArray] = None
    ) -> NDArray:
        """Perform inference to update beliefs given observation.

        Args:
            observation: Observed data
            prior_beliefs: Prior beliefs (uses D if None)

        Returns:
            Posterior beliefs over hidden states
        """
        try:
            prior = prior_beliefs if prior_beliefs is not None else self.D

            # Simple Bayesian inference: posterior ∝ likelihood × prior
            likelihood = (
                self.A[observation.argmax()]
                if len(observation.shape) > 0
                else self.A[0]
            )
            posterior = likelihood * prior

            # Normalize
            posterior = np.clip(posterior, 1e-10, 1.0)
            posterior = posterior / posterior.sum()

            return posterior

        except Exception as e:
            logger.error(f"Error performing inference: {e}")
            raise ValidationError(f"Inference failed: {e}") from e

    def demonstrate_modeler_specifications(self) -> Dict[str, Union[str, Dict]]:
        """Demonstrate how the modeler specifies different aspects of the agent.

        Returns:
            Dictionary showing modeler specification examples
        """
        specifications = {
            "epistemic_specification": {
                "generative_model_design": """
                The modeler specifies the agent's epistemic framework through matrices A and D.
                A defines how states generate observations (what the agent can know).
                D defines prior beliefs (what the agent assumes initially).
                """,
                "matrix_A_role": "Defines observation likelihoods - what is knowable",
                "matrix_D_role": "Defines prior knowledge - initial assumptions",
                "modeler_power": "Complete control over epistemic boundaries and assumptions",
            },
            "pragmatic_specification": {
                "description": """
                The modeler specifies pragmatic considerations through matrix C.
                C defines preference priors (what outcomes are desired or avoided).
                This enables specification of particular pragmatic frameworks.
                """,
                "matrix_C_role": "Defines value/goal structure - what matters to the agent",
                "pragmatic_framework": "Modeler defines the pragmatic landscape",
                "meta_pragmatic": "Modeler specifies pragmatic considerations for the modeled entity",
            },
            "dynamic_specification": {
                "description": """
                The modeler specifies system dynamics through matrix B.
                B defines how actions influence state transitions.
                This controls the agent's ability to influence its world.
                """,
                "matrix_B_role": "Defines action consequences - what the agent can control",
                "intervention_power": "Modeler specifies causal relationships",
                "agency_framework": "Modeler defines the boundaries of agency",
            },
            "meta_level_implications": {
                "epistemic_meta": """
                By specifying A and D, the modeler defines not just what the agent believes,
                but the very structure of how those beliefs are formed. This is meta-epistemic
                because it specifies the epistemic framework within which the agent operates.
                """,
                "pragmatic_meta": """
                By specifying C, the modeler defines particular pragmatic considerations
                for the modeled entity. This is meta-pragmatic because it allows specification
                of pragmatic frameworks beyond simple reward functions.
                """,
            },
        }

        logger.info(
            "Demonstrated modeler specification capabilities in generative models"
        )
        return specifications


def create_simple_generative_model() -> GenerativeModel:
    """Create a simple generative model for demonstration.

    Returns:
        Simple GenerativeModel instance with basic matrices
    """
    # Simple 2-state, 2-observation, 2-action model
    n_states = 2
    n_observations = 2
    n_actions = 2

    # A: Observation likelihoods P(o|s)
    # State 0 likely generates observation 0, state 1 generates observation 1
    A = np.array(
        [[0.8, 0.2], [0.2, 0.8]]  # P(o=0|s=0), P(o=0|s=1)  # P(o=1|s=0), P(o=1|s=1)
    )

    # B: Transition probabilities P(s'|s,a)
    # Action 0: stay in current state, Action 1: switch states
    B = np.zeros((n_states, n_states, n_actions))
    B[:, :, 0] = np.eye(n_states)  # Stay action
    B[:, :, 1] = np.fliplr(np.eye(n_states))  # Switch action

    # C: Preferences - prefer observation 0, avoid observation 1
    C = np.array([1.0, -1.0])  # log preferences

    # D: Prior beliefs - equal probability
    D = np.array([0.5, 0.5])

    return GenerativeModel(A, B, C, D)


def demonstrate_generative_model_concepts() -> Dict[str, Union[str, Dict]]:
    """Demonstrate key generative model concepts and their roles.

    Returns:
        Dictionary containing demonstrations and explanations
    """
    # Create simple model
    model = create_simple_generative_model()

    # Demonstrate inference
    observation = np.array([1.0, 0.0])  # Observed state 0
    posterior = model.perform_inference(observation)

    # Demonstrate prediction
    predicted_obs = model.predict_observations(0)  # From state 0

    # Demonstrate transition
    next_state = model.predict_state_transition(0, 1)  # State 0 + Action 1

    # Demonstrate preferences
    pref_obs_0 = model.calculate_preference_likelihood(0)
    pref_obs_1 = model.calculate_preference_likelihood(1)

    # Modeler specifications
    specifications = model.demonstrate_modeler_specifications()

    demonstration = {
        "model_structure": {
            "n_states": model.n_states,
            "n_observations": model.n_observations,
            "n_actions": model.n_actions,
            "matrices": {
                "A_shape": model.A.shape,
                "B_shape": model.B.shape,
                "C_shape": model.C.shape,
                "D_shape": model.D.shape,
            },
        },
        "inference_demo": {
            "observation": observation.tolist(),
            "posterior_beliefs": posterior.tolist(),
            "inference_interpretation": "Observation favors state 0, posterior reflects this",
        },
        "prediction_demo": {
            "state": 0,
            "predicted_observations": predicted_obs.tolist(),
            "prediction_interpretation": "State 0 most likely generates observation 0",
        },
        "transition_demo": {
            "current_state": 0,
            "action": 1,
            "next_state_distribution": next_state.tolist(),
            "transition_interpretation": "Action 1 switches from state 0 to state 1",
        },
        "preference_demo": {
            "preference_obs_0": pref_obs_0,
            "preference_obs_1": pref_obs_1,
            "preference_interpretation": "System prefers observation 0, avoids observation 1",
        },
        "modeler_specifications": specifications,
        "key_insights": {
            "modeler_power": """
            The generative model framework gives the modeler complete control over
            specifying both epistemic (A, D matrices) and pragmatic (C matrix)
            aspects of the modeled agent.
            """,
            "meta_epistemic": """
            By defining matrices A and D, the modeler specifies not just what the
            agent believes, but the very structure of how beliefs are formed and updated.
            """,
            "meta_pragmatic": """
            By defining matrix C, the modeler specifies particular pragmatic considerations
            for the modeled entity, enabling goal-directed behavior beyond simple rewards.
            """,
            "active_inference_foundation": """
            The A, B, C, D matrices form the foundation of Active Inference,
            enabling perception as inference, EFE calculations, and policy selection.
            """,
        },
    }

    logger.info("Demonstrated generative model concepts with complete working example")
    return demonstration
