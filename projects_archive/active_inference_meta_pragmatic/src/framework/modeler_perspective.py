"""Modeler Perspective Implementation.

This module implements the dual role of the modeler in Active Inference:
1. As architect: Designing and specifying the generative models, epistemic frameworks, and pragmatic considerations
2. As subject: Using Active Inference principles to understand their own cognition

The modeler specifies both epistemic and pragmatic frameworks for modeled entities,
making Active Inference fundamentally meta-epistemic and meta-pragmatic.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from numpy.typing import NDArray
from ..utils.exceptions import ValidationError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ModelerPerspective:
    """Implementation of the modeler's dual role in Active Inference.

    The modeler operates both as an architect (designing agent models) and as
    a subject (understanding their own cognition through Active Inference principles).
    """

    def __init__(self) -> None:
        """Initialize modeler perspective framework."""
        self.specified_frameworks: Dict[str, Dict] = {}
        self.self_reflective_insights: List[Dict] = []

        logger.info("Initialized modeler perspective framework")

    def specify_epistemic_framework(
        self, framework_name: str, epistemic_boundaries: Dict[str, Union[str, List]]
    ) -> Dict[str, Union[str, Dict]]:
        """Specify an epistemic framework for a modeled agent.

        Args:
            framework_name: Name of the epistemic framework
            epistemic_boundaries: Definition of epistemic boundaries and constraints

        Returns:
            Dictionary containing the specified epistemic framework
        """
        try:
            if not framework_name or not framework_name.strip():
                raise ValueError("Framework name cannot be empty")

            if not epistemic_boundaries:
                raise ValueError("Epistemic boundaries cannot be empty")

            epistemic_framework = {
                "framework_name": framework_name,
                "epistemic_boundaries": epistemic_boundaries,
                "meta_epistemic_nature": """
                By specifying this framework, the modeler defines not just what the agent
                believes, but the very structure of how those beliefs are formed and updated.
                This makes Active Inference meta-epistemic.
                """,
                "specification_power": """
                The modeler has complete control over defining:
                - What is knowable (observation likelihoods)
                - Initial assumptions (prior beliefs)
                - Learning mechanisms (belief updating rules)
                """,
                "framework_type": "epistemic",
            }

            self.specified_frameworks[framework_name] = epistemic_framework

            logger.info(f"Specified epistemic framework: {framework_name}")
            return epistemic_framework

        except Exception as e:
            logger.error(f"Error specifying epistemic framework: {e}")
            raise ValidationError(
                f"Epistemic framework specification failed: {e}"
            ) from e

    def specify_pragmatic_framework(
        self, framework_name: str, pragmatic_considerations: Dict[str, Union[str, List]]
    ) -> Dict[str, Union[str, Dict]]:
        """Specify a pragmatic framework for a modeled agent.

        Args:
            framework_name: Name of the pragmatic framework
            pragmatic_considerations: Definition of pragmatic goals and values

        Returns:
            Dictionary containing the specified pragmatic framework
        """
        try:
            if not framework_name or not framework_name.strip():
                raise ValueError("Framework name cannot be empty")

            if not pragmatic_considerations:
                raise ValueError("Pragmatic considerations cannot be empty")

            pragmatic_framework = {
                "framework_name": framework_name,
                "pragmatic_considerations": pragmatic_considerations,
                "meta_pragmatic_nature": """
                By specifying this framework, the modeler defines particular pragmatic
                considerations for the modeled entity, going beyond simple reward functions
                to include complex value structures and goal hierarchies.
                """,
                "specification_power": """
                The modeler defines:
                - What matters to the agent (preference structure)
                - Goal hierarchies and value systems
                - Trade-offs between different pragmatic considerations
                """,
                "framework_type": "pragmatic",
            }

            self.specified_frameworks[framework_name] = pragmatic_framework

            logger.info(f"Specified pragmatic framework: {framework_name}")
            return pragmatic_framework

        except Exception as e:
            logger.error(f"Error specifying pragmatic framework: {e}")
            raise ValidationError(
                f"Pragmatic framework specification failed: {e}"
            ) from e

    def demonstrate_meta_epistemic_modeling(self) -> Dict[str, Union[str, Dict]]:
        """Demonstrate meta-epistemic aspects of Active Inference modeling.

        Returns:
            Dictionary containing meta-epistemic demonstrations
        """
        demonstrations = {
            "epistemic_framework_specification": {
                "generative_model_design": """
                The modeler specifies matrices A and D, defining what the agent can know
                and what it assumes initially. This goes beyond specifying beliefs to
                defining the epistemic framework within which beliefs operate.
                """,
                "observation_likelihoods_A": """
                Matrix A defines P(o|s) - the observation likelihoods. The modeler
                specifies what sensory information is available and how reliably
                it indicates hidden states.
                """,
                "prior_beliefs_D": """
                Matrix D defines P(s) - the prior beliefs. The modeler specifies
                initial assumptions and biases that shape all subsequent learning.
                """,
                "inference_structure": """
                The modeler specifies the inference algorithms and belief updating
                rules, defining how the agent comes to know its world.
                """,
            },
            "meta_epistemic_implications": {
                "framework_definition": """
                Active Inference is meta-epistemic because it allows modelers to
                specify the epistemic frameworks within which agents operate,
                not just their current beliefs.
                """,
                "knowledge_architecture": """
                The modeler defines the architecture of knowledge itself - how
                information flows, how beliefs are structured, and how learning occurs.
                """,
                "epistemic_boundaries": """
                By designing generative models, the modeler sets the fundamental
                boundaries of what can be known and how knowledge is acquired.
                """,
            },
        }

        logger.info("Demonstrated meta-epistemic modeling capabilities")
        return demonstrations

    def demonstrate_meta_pragmatic_modeling(self) -> Dict[str, Union[str, Dict]]:
        """Demonstrate meta-pragmatic aspects of Active Inference modeling.

        Returns:
            Dictionary containing meta-pragmatic demonstrations
        """
        demonstrations = {
            "pragmatic_framework_specification": {
                "preference_structure_C": """
                Matrix C defines the preference structure - what outcomes are desired
                or avoided. The modeler specifies the value system that drives behavior.
                """,
                "goal_hierarchies": """
                Beyond simple rewards, the modeler can specify complex goal hierarchies,
                trade-offs between short-term and long-term objectives, and nuanced
                value structures.
                """,
                "expected_free_energy": """
                EFE combines epistemic (information gain) and pragmatic (goal achievement)
                components, allowing the modeler to specify how these trade off.
                """,
            },
            "meta_pragmatic_implications": {
                "pragmatic_specification": """
                Active Inference is meta-pragmatic because it enables modelers to
                specify particular pragmatic considerations for modeled entities,
                going beyond simple reinforcement learning reward functions.
                """,
                "value_system_design": """
                The modeler designs complete value systems, including how different
                goals interact, how preferences evolve, and how actions serve multiple
                objectives simultaneously.
                """,
                "decision_framework": """
                By specifying EFE structure, the modeler defines the fundamental
                framework within which decisions are made and actions selected.
                """,
            },
        }

        logger.info("Demonstrated meta-pragmatic modeling capabilities")
        return demonstrations

    def analyze_self_reflective_modeling(self) -> Dict[str, Union[str, Dict]]:
        """Analyze the self-reflective aspect of using Active Inference to model oneself.

        Returns:
            Dictionary containing self-reflective analysis
        """
        analysis = {
            "dual_role_of_modeler": {
                "architect_role": """
                As architect, the modeler designs generative models, specifies epistemic
                and pragmatic frameworks, and defines the boundaries of agent cognition.
                """,
                "subject_role": """
                As subject, the modeler applies Active Inference principles to understand
                their own cognition, using the same frameworks they design for others.
                """,
                "recursive_modeling": """
                This creates recursive modeling: we model ourselves using the same
                principles we use to model others, leading to meta-level insights.
                """,
            },
            "self_understanding_through_modeling": {
                "cognitive_self_modeling": """
                By modeling artificial agents, we gain insights into our own cognitive
                processes. The frameworks we design reveal assumptions about cognition.
                """,
                "epistemic_self_reflection": """
                Designing epistemic frameworks forces us to confront our own assumptions
                about knowledge, belief formation, and learning mechanisms.
                """,
                "pragmatic_self_reflection": """
                Specifying pragmatic frameworks requires us to articulate our own
                value systems, goals, and decision-making processes.
                """,
            },
            "meta_theoretical_insights": {
                "frameworks_as_tools": """
                Active Inference frameworks become tools for self-understanding,
                enabling meta-theoretical analysis of cognitive processes.
                """,
                "recursive_understanding": """
                We understand cognition by modeling it, then understand our modeling
                by applying the same principles to ourselves, creating recursive insight.
                """,
                "unified_perspective": """
                This dual role provides a unified perspective on cognition, bridging
                the gap between modeling others and understanding ourselves.
                """,
            },
        }

        # Store self-reflective insights
        self.self_reflective_insights.append(
            {
                "timestamp": "current",
                "analysis": analysis,
                "insights": [
                    "Active Inference enables recursive self-understanding",
                    "Modeling others reveals assumptions about cognition",
                    "Meta-epistemic and meta-pragmatic frameworks apply to self-modeling",
                ],
            }
        )

        logger.info("Analyzed self-reflective aspects of Active Inference modeling")
        return analysis

    def demonstrate_modeler_specifications(self) -> Dict[str, Union[str, List, Dict]]:
        """Demonstrate the modeler's power to specify agent characteristics.

        Returns:
            Dictionary containing specification demonstrations
        """
        # Create example frameworks
        epistemic_spec = self.specify_epistemic_framework(
            "scientific_epistemology",
            {
                "observation_model": ["reliable_sensors", "measurement_error"],
                "prior_knowledge": ["domain_expertise", "initial_assumptions"],
                "learning_mechanisms": ["bayesian_inference", "parameter_estimation"],
            },
        )

        pragmatic_spec = self.specify_pragmatic_framework(
            "goal_directed_behavior",
            {
                "primary_goals": ["information_seeking", "resource_acquisition"],
                "value_tradeoffs": ["exploration_vs_exploitation", "risk_vs_reward"],
                "decision_horizons": ["short_term", "long_term", "hierarchical"],
            },
        )

        specifications = {
            "epistemic_specifications": epistemic_spec,
            "pragmatic_specifications": pragmatic_spec,
            "modeler_power_demonstration": {
                "epistemic_control": """
                The modeler completely controls the agent's epistemic framework:
                what can be known, how knowledge is acquired, and how beliefs are updated.
                """,
                "pragmatic_control": """
                The modeler specifies the agent's pragmatic landscape:
                what goals matter, how values are structured, and how decisions are made.
                """,
                "meta_level_control": """
                This control operates at meta-levels, defining frameworks within
                which epistemic and pragmatic processes operate.
                """,
            },
            "implications_for_cognitive_science": {
                "framework_flexibility": """
                Active Inference provides flexible frameworks for modeling diverse
                cognitive architectures and decision-making strategies.
                """,
                "unified_account": """
                The same mathematical framework can model perception, learning,
                decision-making, and action in a unified manner.
                """,
                "meta_theoretical_power": """
                The meta-epistemic and meta-pragmatic nature enables modeling
                of how different cognitive systems know and value.
                """,
            },
        }

        logger.info("Demonstrated modeler specification capabilities and implications")
        return specifications

    def synthesize_meta_theoretical_perspective(self) -> Dict[str, Union[str, Dict]]:
        """Synthesize the meta-theoretical perspective on Active Inference.

        Returns:
            Dictionary containing the complete meta-theoretical synthesis
        """
        synthesis = {
            "core_thesis": """
            Considered as a tradition of action and inquiry, Active Inference is
            pragmatic and epistemic (evident from Expected Free Energy) and
            meta-pragmatic and meta-epistemic (evident from the method in use).
            """,
            "quadrant_analysis": {
                "quadrant_1_basis": """
                Data processing at cognitive level provides baseline pragmatic
                and epistemic functioning through EFE minimization.
                """,
                "quadrant_2_enhancement": """
                Meta-data organization enhances epistemic processing while
                maintaining cognitive-level operation.
                """,
                "quadrant_3_reflection": """
                Data processing at meta-cognitive level enables self-monitoring
                and adaptive control of cognitive processes.
                """,
                "quadrant_4_higher_reasoning": """
                Meta-data processing at meta-cognitive level enables framework-level
                reasoning about cognition itself.
                """,
            },
            "modeler_dual_role": {
                "architect_perspective": """
                As architect, the modeler specifies generative models that define
                epistemic and pragmatic frameworks for modeled entities.
                """,
                "subject_perspective": """
                As subject, the modeler applies these same principles to understand
                their own cognition, creating recursive self-understanding.
                """,
                "unified_framework": """
                This dual role provides a unified framework for understanding
                cognition across different levels of abstraction.
                """,
            },
            "cognitive_security_implications": {
                "meta_cognitive_vulnerability": """
                Understanding meta-cognitive processes reveals potential vulnerabilities
                in higher-order reasoning and framework-level manipulation.
                """,
                "epistemic_framework_manipulation": """
                Meta-epistemic awareness enables defense against attempts to
                manipulate belief formation and knowledge structures.
                """,
                "pragmatic_framework_protection": """
                Meta-pragmatic understanding allows protection of value systems
                and decision-making frameworks from external influence.
                """,
            },
            "free_energy_principle_integration": {
                "unified_thing_definition": """
                FEP provides a unified definition of 'things' as systems that
                maintain structure through free energy minimization.
                """,
                "bridge_physics_cognition": """
                FEP bridges physics and cognition, showing how diverse phenomena
                can be understood through a single theoretical framework.
                """,
                "structure_preservation": """
                Systems maintain their organization by minimizing variational
                free energy, preserving structural integrity over time.
                """,
            },
        }

        logger.info(
            "Synthesized complete meta-theoretical perspective on Active Inference"
        )
        return synthesis


def demonstrate_modeler_perspective() -> Dict[str, Union[str, Dict]]:
    """Demonstrate the complete modeler perspective framework.

    Returns:
        Dictionary containing comprehensive demonstrations
    """
    modeler = ModelerPerspective()

    # Demonstrate framework specifications
    specifications = modeler.demonstrate_modeler_specifications()

    # Demonstrate meta-epistemic and meta-pragmatic aspects
    meta_epistemic = modeler.demonstrate_meta_epistemic_modeling()
    meta_pragmatic = modeler.demonstrate_meta_pragmatic_modeling()

    # Analyze self-reflective modeling
    self_reflection = modeler.analyze_self_reflective_modeling()

    # Synthesize complete perspective
    synthesis = modeler.synthesize_meta_theoretical_perspective()

    demonstration = {
        "modeler_specifications": specifications,
        "meta_epistemic_demonstration": meta_epistemic,
        "meta_pragmatic_demonstration": meta_pragmatic,
        "self_reflective_analysis": self_reflection,
        "meta_theoretical_synthesis": synthesis,
        "key_insights": {
            "meta_epistemic_power": """
            Active Inference enables modelers to specify epistemic frameworks,
            defining how agents know their world, not just what they believe.
            """,
            "meta_pragmatic_power": """
            Active Inference enables modelers to specify pragmatic frameworks,
            defining what matters to agents beyond simple rewards.
            """,
            "recursive_self_understanding": """
            The dual role creates recursive understanding: modeling others
            reveals insights about our own cognition.
            """,
            "unified_cognitive_framework": """
            Active Inference provides a unified mathematical framework for
            understanding perception, action, learning, and cognition.
            """,
        },
    }

    logger.info("Demonstrated complete modeler perspective with all aspects")
    return demonstration
