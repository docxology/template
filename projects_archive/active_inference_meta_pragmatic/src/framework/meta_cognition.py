"""Meta-Cognition Implementation.

This module implements meta-cognitive concepts central to understanding
'thinking about thinking' in Active Inference. Meta-cognition involves:

- Self-assessment of confidence in inferences
- Adjustment of attention and action regimes
- Evaluation of cognitive processes themselves
- Higher-order control of cognitive strategies

Meta-cognition enables agents to monitor and regulate their own cognitive processes,
leading to more adaptive and robust behavior.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from numpy.typing import NDArray
from ..utils.exceptions import ValidationError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class MetaCognitiveSystem:
    """Implementation of meta-cognitive monitoring and control.

    Meta-cognition involves monitoring one's own cognitive processes and
    making adjustments to improve performance and adapt to changing conditions.
    """

    def __init__(
        self, confidence_threshold: float = 0.7, adaptation_rate: float = 0.1
    ) -> None:
        """Initialize meta-cognitive system.

        Args:
            confidence_threshold: Threshold for triggering meta-cognitive evaluation
            adaptation_rate: Rate of meta-cognitive adaptation
        """
        self.confidence_threshold = confidence_threshold
        self.adaptation_rate = adaptation_rate

        # Meta-cognitive state tracking
        self.confidence_history: List[float] = []
        self.attention_allocation: Dict[str, float] = {}
        self.strategy_effectiveness: Dict[str, float] = {}

        logger.info(
            f"Initialized meta-cognitive system with confidence threshold {confidence_threshold}"
        )

    def assess_inference_confidence(
        self, posterior_beliefs: NDArray, observation_uncertainty: float
    ) -> Dict[str, Union[float, str]]:
        """Assess confidence in current inference results.

        Args:
            posterior_beliefs: Current posterior belief distribution
            observation_uncertainty: Uncertainty in observation data

        Returns:
            Dictionary containing confidence metrics and assessment
        """
        try:
            # Calculate confidence metrics
            entropy = self._calculate_belief_entropy(posterior_beliefs)
            max_belief = np.max(posterior_beliefs)
            belief_spread = np.std(posterior_beliefs)

            # Composite confidence score
            confidence_score = self._calculate_confidence_score(
                entropy, max_belief, belief_spread, observation_uncertainty
            )

            # Store in history
            self.confidence_history.append(confidence_score)

            assessment = {
                "confidence_score": confidence_score,
                "entropy": entropy,
                "max_belief": max_belief,
                "belief_spread": belief_spread,
                "observation_uncertainty": observation_uncertainty,
                "assessment": self._interpret_confidence(confidence_score),
                "needs_meta_evaluation": confidence_score < self.confidence_threshold,
            }

            logger.debug(f"Assessed inference confidence: {confidence_score:.3f}")
            return assessment

        except Exception as e:
            logger.error(f"Error assessing inference confidence: {e}")
            raise ValidationError(f"Confidence assessment failed: {e}") from e

    def _calculate_belief_entropy(self, beliefs: NDArray) -> float:
        """Calculate entropy of belief distribution."""
        beliefs = np.clip(beliefs, 1e-10, 1.0)
        return -np.sum(beliefs * np.log(beliefs))

    def _calculate_confidence_score(
        self,
        entropy: float,
        max_belief: float,
        belief_spread: float,
        obs_uncertainty: float,
    ) -> float:
        """Calculate composite confidence score."""
        # Normalize entropy (lower entropy = higher confidence)
        max_entropy = (
            np.log(len(self.confidence_history) + 2) if self.confidence_history else 1.0
        )
        normalized_entropy = 1.0 - (entropy / max_entropy)

        # Combine factors (weighted average)
        confidence = (
            0.4 * max_belief  # Strongest belief
            + 0.3 * normalized_entropy  # Belief certainty
            + 0.2 * (1.0 - belief_spread)  # Belief concentration
            + 0.1 * (1.0 - obs_uncertainty)  # Observation quality
        )

        return float(np.clip(confidence, 0.0, 1.0))

    def _interpret_confidence(self, confidence_score: float) -> str:
        """Interpret confidence score qualitatively."""
        if confidence_score >= 0.8:
            return "High confidence - inference appears reliable"
        elif confidence_score >= 0.6:
            return "Moderate confidence - inference may need verification"
        elif confidence_score >= 0.4:
            return "Low confidence - consider alternative strategies"
        else:
            return "Very low confidence - meta-cognitive intervention required"

    def adjust_attention_allocation(
        self, confidence_assessment: Dict, available_resources: Dict[str, float]
    ) -> Dict[str, float]:
        """Adjust attention allocation based on confidence assessment.

        Args:
            confidence_assessment: Results from confidence assessment
            available_resources: Available cognitive resources by type

        Returns:
            Updated attention allocation across cognitive processes
        """
        try:
            confidence_score = confidence_assessment["confidence_score"]

            # Validate inputs
            if not available_resources:
                raise ValidationError("Available resources cannot be empty")

            # Base allocation
            base_allocation = {
                k: 1.0 / len(available_resources) for k in available_resources.keys()
            }

            # Adjust based on confidence
            if confidence_score < self.confidence_threshold:
                # Low confidence - increase meta-cognitive monitoring
                adjustments = {
                    "inference_monitoring": 1.5,
                    "uncertainty_assessment": 1.3,
                    "strategy_evaluation": 1.2,
                    "basic_processing": 0.8,
                }
            else:
                # High confidence - maintain efficient allocation
                adjustments = {
                    "inference_monitoring": 1.0,
                    "uncertainty_assessment": 1.0,
                    "strategy_evaluation": 1.0,
                    "basic_processing": 1.0,
                }

            # Apply adjustments
            updated_allocation = {}
            for resource, base_weight in base_allocation.items():
                adjustment = adjustments.get(resource, 1.0)
                updated_allocation[resource] = base_weight * adjustment

            # Normalize to ensure sum = 1
            total = sum(updated_allocation.values())
            updated_allocation = {k: v / total for k, v in updated_allocation.items()}

            # Update internal state
            self.attention_allocation = updated_allocation

            logger.debug(f"Adjusted attention allocation: {updated_allocation}")
            return updated_allocation

        except Exception as e:
            logger.error(f"Error adjusting attention allocation: {e}")
            raise ValidationError(f"Attention allocation adjustment failed: {e}") from e

    def evaluate_strategy_effectiveness(
        self, strategy_name: str, performance_metrics: Dict[str, float]
    ) -> Dict[str, Union[float, str]]:
        """Evaluate effectiveness of cognitive strategies.

        Args:
            strategy_name: Name of the strategy being evaluated
            performance_metrics: Performance metrics for the strategy

        Returns:
            Dictionary containing effectiveness assessment
        """
        try:
            # Calculate composite effectiveness score
            weights = {
                "accuracy": 0.4,
                "efficiency": 0.3,
                "adaptability": 0.2,
                "robustness": 0.1,
            }

            effectiveness_score = sum(
                weights[metric] * performance_metrics.get(metric, 0.5)
                for metric in weights.keys()
            )

            # Update strategy tracking
            self.strategy_effectiveness[strategy_name] = effectiveness_score

            assessment = {
                "strategy": strategy_name,
                "effectiveness_score": effectiveness_score,
                "performance_metrics": performance_metrics,
                "recommendation": self._generate_strategy_recommendation(
                    effectiveness_score, strategy_name
                ),
                "comparison_rank": self._get_strategy_ranking(strategy_name),
            }

            logger.debug(
                f"Evaluated strategy {strategy_name}: effectiveness {effectiveness_score:.3f}"
            )
            return assessment

        except Exception as e:
            logger.error(f"Error evaluating strategy effectiveness: {e}")
            raise ValidationError(f"Strategy evaluation failed: {e}") from e

    def _generate_strategy_recommendation(
        self, effectiveness: float, strategy: str
    ) -> str:
        """Generate recommendation based on strategy effectiveness."""
        if effectiveness >= 0.8:
            return f"Continue using {strategy} - highly effective"
        elif effectiveness >= 0.6:
            return f"Monitor {strategy} performance - moderately effective"
        elif effectiveness >= 0.4:
            return f"Consider alternatives to {strategy} - limited effectiveness"
        else:
            return f"Avoid {strategy} - poor performance, seek alternatives"

    def _get_strategy_ranking(self, strategy: str) -> str:
        """Get ranking of strategy compared to others."""
        if not self.strategy_effectiveness:
            return "First strategy evaluated"

        sorted_strategies = sorted(
            self.strategy_effectiveness.items(), key=lambda x: x[1], reverse=True
        )

        rank = next(
            i + 1 for i, (name, _) in enumerate(sorted_strategies) if name == strategy
        )
        total = len(sorted_strategies)

        return f"Rank {rank}/{total} among evaluated strategies"

    def implement_meta_cognitive_control(
        self, current_state: Dict, meta_cognitive_assessment: Dict
    ) -> Dict[str, Union[str, Dict]]:
        """Implement meta-cognitive control based on current state and assessment.

        Args:
            current_state: Current cognitive system state
            meta_cognitive_assessment: Results from meta-cognitive evaluation

        Returns:
            Dictionary containing control actions and rationale
        """
        try:
            control_actions = {
                "attention_adjustment": {},
                "strategy_selection": "",
                "processing_modulation": {},
                "monitoring_intensity": "normal",
            }

            confidence_score = meta_cognitive_assessment.get("confidence_score", 1.0)

            if confidence_score < 0.3:
                # Critical low confidence - intensive intervention
                control_actions.update(
                    {
                        "attention_adjustment": {
                            "monitoring": 2.0,
                            "basic_processing": 0.5,
                        },
                        "strategy_selection": "conservative_inference",
                        "processing_modulation": {
                            "speed": "slow",
                            "thoroughness": "high",
                        },
                        "monitoring_intensity": "intensive",
                    }
                )
            elif confidence_score < 0.6:
                # Moderate low confidence - moderate intervention
                control_actions.update(
                    {
                        "attention_adjustment": {
                            "monitoring": 1.5,
                            "verification": 1.3,
                        },
                        "strategy_selection": "cautious_inference",
                        "processing_modulation": {"thoroughness": "increased"},
                        "monitoring_intensity": "elevated",
                    }
                )
            else:
                # Normal confidence - maintain efficient processing
                control_actions.update(
                    {
                        "attention_adjustment": {"efficiency": 1.2},
                        "strategy_selection": "standard_inference",
                        "processing_modulation": {
                            "speed": "normal",
                            "thoroughness": "balanced",
                        },
                        "monitoring_intensity": "normal",
                    }
                )

            control_decision = {
                "control_actions": control_actions,
                "rationale": self._generate_control_rationale(confidence_score),
                "expected_outcomes": self._predict_control_outcomes(control_actions),
                "monitoring_plan": "Continuous assessment with adaptive thresholds",
            }

            logger.info(
                f"Implemented meta-cognitive control: {control_actions['monitoring_intensity']} intensity"
            )
            return control_decision

        except Exception as e:
            logger.error(f"Error implementing meta-cognitive control: {e}")
            raise ValidationError(
                f"Meta-cognitive control implementation failed: {e}"
            ) from e

    def _generate_control_rationale(self, confidence_score: float) -> str:
        """Generate rationale for control decisions."""
        if confidence_score < 0.3:
            return "Critical confidence levels require intensive meta-cognitive intervention to ensure reliable processing"
        elif confidence_score < 0.6:
            return "Moderate confidence concerns warrant increased monitoring and cautious processing strategies"
        else:
            return "Normal confidence levels support efficient processing with standard meta-cognitive oversight"

    def _predict_control_outcomes(self, control_actions: Dict) -> Dict[str, str]:
        """Predict expected outcomes of control actions."""
        monitoring = control_actions.get("monitoring_intensity", "normal")

        outcomes = {
            "intensive": {
                "confidence": "Expected improvement through increased monitoring",
                "efficiency": "Reduced efficiency due to intensive processing",
                "reliability": "High reliability through comprehensive oversight",
            },
            "elevated": {
                "confidence": "Moderate confidence improvement",
                "efficiency": "Slight efficiency reduction",
                "reliability": "Enhanced reliability with focused monitoring",
            },
            "normal": {
                "confidence": "Maintained confidence levels",
                "efficiency": "Optimal efficiency",
                "reliability": "Standard reliability with routine monitoring",
            },
        }

        return outcomes.get(monitoring, outcomes["normal"])

    def demonstrate_meta_cognitive_processes(self) -> Dict[str, Union[str, List, Dict]]:
        """Demonstrate meta-cognitive processes and their operation.

        Returns:
            Dictionary containing demonstrations of meta-cognitive capabilities
        """
        # Simulate a scenario with varying confidence
        scenarios = [
            {
                "name": "High Confidence Scenario",
                "beliefs": np.array([0.9, 0.05, 0.05]),
                "uncertainty": 0.1,
            },
            {
                "name": "Moderate Confidence Scenario",
                "beliefs": np.array([0.6, 0.3, 0.1]),
                "uncertainty": 0.3,
            },
            {
                "name": "Low Confidence Scenario",
                "beliefs": np.array([0.4, 0.3, 0.3]),
                "uncertainty": 0.7,
            },
        ]

        demonstrations = []

        for scenario in scenarios:
            assessment = self.assess_inference_confidence(
                scenario["beliefs"], scenario["uncertainty"]
            )

            attention = self.adjust_attention_allocation(
                assessment, {"monitoring": 1.0, "processing": 1.0, "evaluation": 1.0}
            )

            control = self.implement_meta_cognitive_control(
                {"current_beliefs": scenario["beliefs"]}, assessment
            )

            demonstrations.append(
                {
                    "scenario": scenario["name"],
                    "assessment": assessment,
                    "attention_allocation": attention,
                    "control_decision": control,
                }
            )

        meta_cognitive_explanation = {
            "core_concept": """
            Meta-cognition enables 'thinking about thinking' - the ability to monitor,
            evaluate, and control one's own cognitive processes. In Active Inference,
            this manifests as confidence assessment, attention regulation, and adaptive
            strategy selection.
            """,
            "active_inference_role": """
            Meta-cognition in Active Inference involves evaluating the reliability of
            inferences and adjusting processing strategies accordingly. Low confidence
            triggers increased monitoring and more conservative decision-making.
            """,
            "quadrant_placement": """
            Meta-cognition primarily operates in Quadrant 3 (Data & Meta-Cognitive)
            for reflective processing of raw data, and extends to Quadrant 4
            (Meta-Data & Meta-Cognitive) for processing meta-data about meta-cognition.
            """,
        }

        demonstration_results = {
            "scenarios": demonstrations,
            "meta_cognitive_explanation": meta_cognitive_explanation,
            "key_insights": {
                "adaptive_control": "Meta-cognition enables dynamic adjustment of cognitive strategies based on confidence",
                "self_monitoring": "Continuous self-assessment prevents overconfidence and enables error detection",
                "resource_allocation": "Attention and processing resources are allocated based on meta-cognitive evaluation",
                "robustness": "Meta-cognitive control increases system robustness in uncertain environments",
            },
        }

        logger.info("Demonstrated meta-cognitive processes across confidence scenarios")
        return demonstration_results


def demonstrate_meta_cognitive_processes() -> Dict[str, Union[str, List, Dict]]:
    """Demonstrate meta-cognitive processes and their operation.

    Convenience function that creates a MetaCognitiveSystem instance
    and delegates to its demonstrate_meta_cognitive_processes method.

    Returns:
        Dictionary containing demonstrations of meta-cognitive capabilities
    """
    system = MetaCognitiveSystem()
    return system.demonstrate_meta_cognitive_processes()


def demonstrate_thinking_about_thinking() -> Dict[str, str]:
    """Demonstrate the concept of 'thinking about thinking' in Active Inference.

    Returns:
        Dictionary explaining meta-cognitive concepts
    """
    concepts = {
        "meta_cognition_definition": """
        Meta-cognition is cognition about cognition - thinking about one's own
        thinking processes. In Active Inference, this involves monitoring the
        quality and reliability of inferences, evaluating cognitive strategies,
        and adjusting processing approaches based on self-assessment.
        """,
        "confidence_assessment": """
        Agents assess their confidence in inferences by evaluating belief entropy,
        maximum belief strength, belief distribution spread, and observation
        uncertainty. Low confidence triggers meta-cognitive interventions.
        """,
        "attention_regulation": """
        Based on confidence assessments, meta-cognitive systems regulate attention
        allocation across different cognitive processes, increasing monitoring
        when confidence is low and optimizing efficiency when confidence is high.
        """,
        "strategy_evaluation": """
        Meta-cognition enables evaluation of different cognitive strategies,
        comparing their effectiveness and selecting appropriate approaches
        for different situations and confidence levels.
        """,
        "self_reflective_processing": """
        Self-reflective processing allows agents to evaluate their own cognitive
        processes, identify potential errors or biases, and implement corrective
        measures to improve performance and reliability.
        """,
        "adaptive_control": """
        Meta-cognitive control enables adaptive regulation of cognitive processing,
        adjusting speed, thoroughness, and resource allocation based on current
        needs and confidence levels.
        """,
    }

    return concepts
