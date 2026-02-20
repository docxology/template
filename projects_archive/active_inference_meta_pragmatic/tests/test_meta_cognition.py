"""Tests for Meta-Cognition Implementation.

Comprehensive tests for meta-cognitive processes including confidence assessment,
attention allocation, strategy evaluation, and self-reflective capabilities.
"""

import numpy as np
import pytest
from src.framework.meta_cognition import (MetaCognitiveSystem,
                                          demonstrate_meta_cognitive_processes,
                                          demonstrate_thinking_about_thinking)
from src.analysis.validation import ValidationFramework


class TestMetaCognitiveSystem:
    """Test Meta-Cognitive System core functionality."""

    @pytest.fixture
    def meta_system(self):
        """Create meta-cognitive system instance."""
        return MetaCognitiveSystem()

    def test_initialization(self, meta_system):
        """Test system initialization."""
        assert meta_system.confidence_threshold == 0.7
        assert meta_system.adaptation_rate == 0.1
        assert meta_system.confidence_history == []
        assert meta_system.attention_allocation == {}
        assert meta_system.strategy_effectiveness == {}

    def test_confidence_assessment(self, meta_system):
        """Test confidence assessment."""
        # High confidence scenario - very strong belief with low uncertainty
        high_conf_beliefs = np.array([0.95, 0.03, 0.02])
        assessment = meta_system.assess_inference_confidence(high_conf_beliefs, 0.05)

        assert "confidence_score" in assessment
        assert "entropy" in assessment
        assert assessment["confidence_score"] > 0.8  # High confidence
        assert (
            assessment["assessment"] == "High confidence - inference appears reliable"
        )

        # Low confidence scenario
        low_conf_beliefs = np.array([0.4, 0.3, 0.3])
        assessment = meta_system.assess_inference_confidence(low_conf_beliefs, 0.7)

        assert assessment["confidence_score"] < 0.5  # Low confidence
        assert assessment["needs_meta_evaluation"] is True

    def test_attention_allocation(self, meta_system):
        """Test attention allocation based on confidence."""
        # Low confidence scenario
        low_conf_assessment = {
            "confidence_score": 0.4,
            "entropy": 1.0,
            "max_belief": 0.5,
        }

        available_resources = {
            "inference_monitoring": 1.0,
            "basic_processing": 1.0,
            "evaluation": 1.0,
        }

        allocation = meta_system.adjust_attention_allocation(
            low_conf_assessment, available_resources
        )

        # Should increase inference_monitoring for low confidence
        assert allocation["inference_monitoring"] > allocation["basic_processing"]
        assert abs(sum(allocation.values()) - 1.0) < 1e-6  # Should sum to 1

        # Update internal state
        assert meta_system.attention_allocation == allocation

    def test_strategy_evaluation(self, meta_system):
        """Test strategy effectiveness evaluation."""
        strategy_metrics = {
            "accuracy": 0.85,
            "efficiency": 0.9,
            "adaptability": 0.75,
            "robustness": 0.8,
        }

        evaluation = meta_system.evaluate_strategy_effectiveness(
            "test_strategy", strategy_metrics
        )

        assert "strategy" in evaluation
        assert "effectiveness_score" in evaluation
        assert "recommendation" in evaluation
        assert evaluation["strategy"] == "test_strategy"
        assert 0 <= evaluation["effectiveness_score"] <= 1

        # Should be recommended for good performance
        assert "Continue using" in evaluation["recommendation"]

    def test_meta_cognitive_control(self, meta_system):
        """Test meta-cognitive control implementation."""
        current_state = {"current_beliefs": np.array([0.5, 0.3, 0.2])}
        meta_assessment = {"confidence_score": 0.6}

        control_decision = meta_system.implement_meta_cognitive_control(
            current_state, meta_assessment
        )

        required_keys = [
            "control_actions",
            "rationale",
            "expected_outcomes",
            "monitoring_plan",
        ]

        for key in required_keys:
            assert key in control_decision

        control_actions = control_decision["control_actions"]
        assert "attention_adjustment" in control_actions
        assert "strategy_selection" in control_actions
        assert "processing_modulation" in control_actions

    def test_error_handling(self, meta_system):
        """Test error handling for invalid inputs."""
        # Invalid belief distribution (negative values) - should handle gracefully by clipping
        result = meta_system.assess_inference_confidence(
            np.array([-0.1, 1.1, 0.0]), 0.1
        )
        assert "confidence_score" in result  # Should still produce a result

        # Empty available resources - should raise ValidationError
        from src.utils.exceptions import ValidationError

        with pytest.raises(ValidationError):
            meta_system.adjust_attention_allocation({"confidence_score": 0.5}, {})


class TestMetaCognitiveDemonstrations:
    """Test meta-cognitive process demonstrations."""

    def test_demonstrate_meta_cognitive_processes(self):
        """Test meta-cognitive process demonstration."""
        demonstration = demonstrate_meta_cognitive_processes()

        required_keys = ["scenarios", "meta_cognitive_explanation", "key_insights"]

        for key in required_keys:
            assert key in demonstration

        # Check scenarios
        scenarios = demonstration["scenarios"]
        assert len(scenarios) == 3  # High, moderate, low confidence

        for scenario in scenarios:
            assert "scenario" in scenario
            assert "assessment" in scenario
            assert "attention_allocation" in scenario
            assert "control_decision" in scenario

    def test_demonstrate_thinking_about_thinking(self):
        """Test 'thinking about thinking' demonstration."""
        concepts = demonstrate_thinking_about_thinking()

        required_concepts = [
            "meta_cognition_definition",
            "confidence_assessment",
            "attention_regulation",
            "strategy_evaluation",
            "self_reflective_processing",
            "adaptive_control",
        ]

        for concept in required_concepts:
            assert concept in concepts
            assert len(concepts[concept]) > 50  # Substantial explanation


class TestMetaCognitiveIntegration:
    """Test meta-cognitive system integration."""

    def test_confidence_history_tracking(self):
        """Test confidence history tracking over time."""
        system = MetaCognitiveSystem()

        # Simulate multiple assessments
        confidence_values = [0.8, 0.6, 0.4, 0.7, 0.5]
        beliefs = np.array([0.5, 0.3, 0.2])

        for conf in confidence_values:
            # Create assessment that will give desired confidence
            uncertainty = max(0, 1 - conf)  # Higher uncertainty = lower confidence
            system.assess_inference_confidence(beliefs, uncertainty)

        assert len(system.confidence_history) == len(confidence_values)

        # History should be tracked correctly
        for i, expected_conf in enumerate(confidence_values):
            # Allow some tolerance due to calculation method
            assert abs(system.confidence_history[i] - expected_conf) < 0.3

    def test_strategy_ranking(self):
        """Test strategy ranking system."""
        system = MetaCognitiveSystem()

        # Add multiple strategies with different performances
        strategies = {
            "strategy_A": {"accuracy": 0.9, "efficiency": 0.8},
            "strategy_B": {"accuracy": 0.7, "efficiency": 0.9},
            "strategy_C": {"accuracy": 0.95, "efficiency": 0.6},
        }

        rankings = {}
        for name, metrics in strategies.items():
            evaluation = system.evaluate_strategy_effectiveness(name, metrics)
            rankings[name] = evaluation["comparison_rank"]

        # Strategy C should rank highest (best accuracy)
        assert "1/" in rankings["strategy_C"]

    def test_adaptive_attention_learning(self):
        """Test adaptive attention learning over time."""
        system = MetaCognitiveSystem()

        # Simulate learning scenario
        scenarios = [
            {
                "beliefs": np.array([0.9, 0.05, 0.05]),
                "uncertainty": 0.1,
            },  # High confidence
            {
                "beliefs": np.array([0.4, 0.3, 0.3]),
                "uncertainty": 0.7,
            },  # Low confidence
            {
                "beliefs": np.array([0.6, 0.3, 0.1]),
                "uncertainty": 0.3,
            },  # Moderate confidence
        ]

        allocations = []
        for scenario in scenarios:
            assessment = system.assess_inference_confidence(
                scenario["beliefs"], scenario["uncertainty"]
            )
            allocation = system.adjust_attention_allocation(
                assessment, {"monitoring": 1.0, "processing": 1.0}
            )
            allocations.append(allocation)

        # Low confidence scenario should have highest monitoring allocation
        low_conf_allocation = allocations[1]  # Second scenario
        assert low_conf_allocation["monitoring"] > low_conf_allocation["processing"]


class TestMetaCognitiveValidation:
    """Test meta-cognitive system validation."""

    @pytest.fixture
    def validator(self):
        """Create validation framework instance."""
        return ValidationFramework()

    def test_meta_cognitive_numerical_stability(self, validator):
        """Test numerical stability of meta-cognitive calculations."""
        system = MetaCognitiveSystem()

        # Test with various inputs
        test_cases = [
            {"beliefs": np.array([0.8, 0.1, 0.1]), "uncertainty": 0.1},
            {"beliefs": np.array([0.5, 0.3, 0.2]), "uncertainty": 0.5},
            {"beliefs": np.array([0.33, 0.33, 0.34]), "uncertainty": 0.9},
        ]

        for case in test_cases:
            assessment = system.assess_inference_confidence(
                case["beliefs"], case["uncertainty"]
            )

            # Validate numerical results
            implementation_result = {
                "confidence_score": assessment["confidence_score"],
                "entropy": assessment["entropy"],
                "max_belief": assessment["max_belief"],
            }

            stability_result = validator._validate_numerical_stability(
                implementation_result
            )
            assert stability_result["stable"] is True

    def test_strategy_effectiveness_validation(self, validator):
        """Test strategy effectiveness evaluation validation."""
        system = MetaCognitiveSystem()

        # Test valid strategy evaluation
        metrics = {
            "accuracy": 0.85,
            "efficiency": 0.9,
            "adaptability": 0.8,
            "robustness": 0.75,
        }

        evaluation = system.evaluate_strategy_effectiveness("test_strategy", metrics)

        # Should produce valid effectiveness score
        assert 0 <= evaluation["effectiveness_score"] <= 1
        assert "recommendation" in evaluation

    def test_attention_allocation_normalization(self, validator):
        """Test attention allocation normalization."""
        system = MetaCognitiveSystem()

        assessment = {"confidence_score": 0.5}
        resources = {"task1": 1.0, "task2": 1.0, "task3": 1.0}

        allocation = system.adjust_attention_allocation(assessment, resources)

        # Should sum to 1
        total_allocation = sum(allocation.values())
        assert abs(total_allocation - 1.0) < 1e-6

        # All values should be positive
        assert all(v >= 0 for v in allocation.values())


class TestMetaCognitiveEdgeCases:
    """Test edge cases in meta-cognitive system."""

    def test_extreme_confidence_values(self):
        """Test extreme confidence values."""
        system = MetaCognitiveSystem()

        # Maximum certainty
        max_certainty = np.array([1.0, 0.0, 0.0])
        assessment = system.assess_inference_confidence(max_certainty, 0.0)

        assert assessment["confidence_score"] > 0.9
        assert assessment["entropy"] < 0.1  # Very low entropy

        # Maximum uncertainty (uniform beliefs + high observation uncertainty)
        max_uncertainty = np.array([0.33, 0.33, 0.34])
        assessment = system.assess_inference_confidence(max_uncertainty, 0.9)

        # Should give low confidence due to high uncertainty
        assert assessment["confidence_score"] < 0.4
        assert assessment["needs_meta_evaluation"] is True

    def test_empty_strategy_history(self):
        """Test behavior with no previous strategy evaluations."""
        system = MetaCognitiveSystem()

        # First strategy evaluation
        evaluation = system.evaluate_strategy_effectiveness(
            "first_strategy", {"accuracy": 0.8, "efficiency": 0.7}
        )

        assert "Rank 1/1" in evaluation["comparison_rank"]

    def test_single_resource_attention(self):
        """Test attention allocation with single resource."""
        system = MetaCognitiveSystem()

        assessment = {"confidence_score": 0.8}
        resources = {"single_task": 1.0}

        allocation = system.adjust_attention_allocation(assessment, resources)

        assert allocation["single_task"] == 1.0

    def test_meta_cognitive_control_extremes(self):
        """Test meta-cognitive control in extreme scenarios."""
        system = MetaCognitiveSystem()

        # Critical scenario
        critical_state = {"current_beliefs": np.array([0.5, 0.5])}
        critical_assessment = {"confidence_score": 0.2}

        control = system.implement_meta_cognitive_control(
            critical_state, critical_assessment
        )

        # Should recommend intensive monitoring
        assert control["control_actions"]["monitoring_intensity"] == "intensive"

        # Normal scenario
        normal_state = {"current_beliefs": np.array([0.9, 0.1])}
        normal_assessment = {"confidence_score": 0.8}

        control = system.implement_meta_cognitive_control(
            normal_state, normal_assessment
        )

        # Should recommend normal monitoring
        assert control["control_actions"]["monitoring_intensity"] == "normal"


class TestMetaCognitiveIntegration:
    """Test meta-cognitive integration with other systems."""

    def test_meta_cognition_with_active_inference(self):
        """Test meta-cognition integration with Active Inference."""
        from src.active_inference import ActiveInferenceFramework
        from src.generative_models import create_simple_generative_model

        # Create AI system
        model = create_simple_generative_model()
        generative_model_dict = {"A": model.A, "B": model.B, "C": model.C, "D": model.D}
        ai_system = ActiveInferenceFramework(generative_model_dict)

        # Create meta-cognitive system
        meta_system = MetaCognitiveSystem()

        # Simulate AI inference
        observation = np.array([0.8, 0.2])
        posterior = ai_system.perception_as_inference(observation)

        # Meta-cognitive assessment
        assessment = meta_system.assess_inference_confidence(posterior, 0.1)

        # Should work together
        assert "confidence_score" in assessment
        assert assessment["confidence_score"] > 0

        # Meta-cognitive control based on AI results
        control = meta_system.implement_meta_cognitive_control(
            {"current_beliefs": posterior}, assessment
        )

        assert "control_actions" in control

    def test_adaptive_strategy_selection(self):
        """Test adaptive strategy selection based on meta-cognitive feedback."""
        system = MetaCognitiveSystem()

        # Simulate strategy performance feedback
        strategies = ["conservative", "balanced", "aggressive"]

        # Conservative performs well in uncertain conditions
        performances = [
            {"accuracy": 0.9, "efficiency": 0.7},  # Conservative
            {"accuracy": 0.6, "efficiency": 0.9},  # Balanced
            {"accuracy": 0.4, "efficiency": 0.95},  # Aggressive
        ]

        for strategy, perf in zip(strategies, performances):
            system.evaluate_strategy_effectiveness(strategy, perf)

        # Conservative should be ranked highest
        conservative_eval = system.evaluate_strategy_effectiveness(
            "conservative", {"accuracy": 0.9, "efficiency": 0.7}
        )

        assert "1/" in conservative_eval["comparison_rank"]
