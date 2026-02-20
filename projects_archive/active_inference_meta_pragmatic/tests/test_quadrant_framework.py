"""Tests for 2x2 Quadrant Framework Implementation.

Comprehensive tests for the quadrant framework including quadrant definitions,
processing level analysis, transitions, and visualization data generation.
"""

import numpy as np
import pytest
from src.framework.quadrant_framework import (QuadrantFramework,
                                               demonstrate_quadrant_framework)
from src.analysis.validation import ValidationFramework


class TestQuadrantFramework:
    """Test Quadrant Framework core functionality."""

    @pytest.fixture
    def quadrant_framework(self):
        """Create quadrant framework instance."""
        return QuadrantFramework()

    def test_initialization(self, quadrant_framework):
        """Test framework initialization."""
        assert quadrant_framework.quadrants is not None
        assert len(quadrant_framework.quadrants) == 4

        expected_quadrant_ids = [
            "Q1_data_cognitive",
            "Q2_metadata_cognitive",
            "Q3_data_metacognitive",
            "Q4_metadata_metacognitive",
        ]

        for qid in expected_quadrant_ids:
            assert qid in quadrant_framework.quadrants

    def test_quadrant_definitions(self, quadrant_framework):
        """Test quadrant definitions are complete."""
        for quadrant_id, quadrant_info in quadrant_framework.quadrants.items():
            required_keys = [
                "name",
                "coordinates",
                "description",
                "examples",
                "examples",
            ]

            for key in required_keys:
                assert key in quadrant_info, f"Missing {key} in {quadrant_id}"

            # Check coordinates
            assert quadrant_info["coordinates"][0] in ["data", "metadata"]
            assert quadrant_info["coordinates"][1] in ["cognitive", "metacognitive"]

            # Check examples structure
            assert "sensemaking_inbound" in quadrant_info["examples"]
            assert "action_outbound" in quadrant_info["examples"]

    def test_get_quadrant(self, quadrant_framework):
        """Test individual quadrant retrieval."""
        # Test valid quadrant
        q1_info = quadrant_framework.get_quadrant("Q1_data_cognitive")
        assert q1_info["name"] == "Data Processing (Cognitive)"
        assert q1_info["coordinates"] == ("data", "cognitive")

        # Test invalid quadrant
        with pytest.raises(Exception):
            quadrant_framework.get_quadrant("invalid_quadrant")

    def test_processing_level_analysis(self, quadrant_framework):
        """Test processing level analysis."""
        # Test all combinations
        test_cases = [
            ("data", "cognitive"),
            ("metadata", "cognitive"),
            ("data", "metacognitive"),
            ("metadata", "metacognitive"),
        ]

        for data_type, cognitive_level in test_cases:
            analysis = quadrant_framework.analyze_processing_level(
                data_type, cognitive_level
            )

            assert "quadrant_id" in analysis
            assert "processing_characteristics" in analysis
            assert "level_assessment" in analysis
            assert "meta_level" in analysis

            # Check quadrant ID format
            quadrant_num = 1 if data_type == "data" else 2
            if cognitive_level == "metacognitive":
                quadrant_num += 2  # Q1->Q3, Q2->Q4
            expected_id = f"Q{quadrant_num}_{data_type}_{cognitive_level}"
            assert analysis["quadrant_id"] == expected_id

            # Check meta level assessment
            meta_analysis = analysis["meta_level"]
            assert "meta_data_level" in meta_analysis
            assert "meta_cognitive_level" in meta_analysis
            assert "overall_meta_level" in meta_analysis

    def test_invalid_processing_level_inputs(self, quadrant_framework):
        """Test error handling for invalid inputs."""
        with pytest.raises(Exception):
            quadrant_framework.analyze_processing_level("invalid", "cognitive")

        with pytest.raises(Exception):
            quadrant_framework.analyze_processing_level("data", "invalid")

    def test_quadrant_transitions(self, quadrant_framework):
        """Test quadrant transition demonstrations."""
        transitions = quadrant_framework.demonstrate_quadrant_transitions()

        required_keys = [
            "developmental_progression",
            "situational_adaptation",
            "learning_progression",
        ]

        for key in required_keys:
            assert key in transitions

        # Check developmental progression
        dev_progression = transitions["developmental_progression"]
        assert len(dev_progression) == 3  # Q1→Q2, Q2→Q3, Q3→Q4

        for transition in dev_progression:
            assert "from" in transition
            assert "to" in transition
            assert "description" in transition

    def test_visualization_data_generation(self, quadrant_framework):
        """Test quadrant matrix visualization data generation."""
        viz_data = quadrant_framework.create_quadrant_matrix_visualization()

        required_keys = [
            "title",
            "subtitle",
            "x_axis",
            "y_axis",
            "quadrants",
            "connections",
        ]

        for key in required_keys:
            assert key in viz_data

        # Check axis definitions
        assert viz_data["x_axis"]["categories"] == ["Data", "Meta-Data"]
        assert viz_data["y_axis"]["categories"] == ["Cognitive", "Meta-Cognitive"]

        # Check quadrant definitions
        quadrants = viz_data["quadrants"]
        assert len(quadrants) == 4

        expected_positions = ["top_left", "top_right", "bottom_left", "bottom_right"]
        for pos in expected_positions:
            assert pos in quadrants
            assert "id" in quadrants[pos]
            assert "name" in quadrants[pos]
            assert "color" in quadrants[pos]


class TestQuadrantDemonstration:
    """Test quadrant framework demonstrations."""

    def test_demonstrate_quadrant_framework(self):
        """Test complete quadrant framework demonstration."""
        demonstration = demonstrate_quadrant_framework()

        required_keys = [
            "framework_overview",
            "quadrant_definitions",
            "level_analysis",
            "transitions",
            "visualization_data",
            "key_insights",
        ]

        for key in required_keys:
            assert key in demonstration

        # Check quadrant definitions
        assert len(demonstration["quadrant_definitions"]) == 4

        # Check level analysis covers all combinations
        level_analysis = demonstration["level_analysis"]
        expected_analyses = [
            "data_cognitive",
            "metadata_cognitive",
            "data_metacognitive",
            "metadata_metacognitive",
        ]

        for analysis_key in expected_analyses:
            assert analysis_key in level_analysis

    def test_level_analysis_completeness(self):
        """Test that level analysis covers all processing levels."""
        demonstration = demonstrate_quadrant_framework()
        level_analysis = demonstration["level_analysis"]

        for analysis_key, analysis in level_analysis.items():
            assert "quadrant_id" in analysis
            assert "processing_characteristics" in analysis
            assert "level_assessment" in analysis
            assert "active_inference_implications" in analysis


class TestQuadrantTransitions:
    """Test quadrant transition logic."""

    @pytest.fixture
    def quadrant_framework(self):
        """Create quadrant framework instance."""
        return QuadrantFramework()

    def test_transition_patterns(self, quadrant_framework):
        """Test transition pattern consistency."""
        transitions = quadrant_framework.demonstrate_quadrant_transitions()

        # Developmental progression should be Q1→Q2→Q3→Q4
        dev_transitions = transitions["developmental_progression"]

        expected_sequence = [
            ("Q1_data_cognitive", "Q2_metadata_cognitive"),
            ("Q2_metadata_cognitive", "Q3_data_metacognitive"),
            ("Q3_data_metacognitive", "Q4_metadata_metacognitive"),
        ]

        for i, (expected_from, expected_to) in enumerate(expected_sequence):
            assert dev_transitions[i]["from"] == expected_from
            assert dev_transitions[i]["to"] == expected_to

    def test_learning_progression(self, quadrant_framework):
        """Test learning progression stages."""
        transitions = quadrant_framework.demonstrate_quadrant_transitions()
        learning = transitions["learning_progression"]

        assert len(learning) == 4  # Novice, competent, expert, master

        stages = ["novice", "competent", "expert", "master"]
        for i, stage_info in enumerate(learning):
            assert stage_info["stage"] == stages[i]
            assert "dominant_quadrant" in stage_info
            assert "characteristics" in stage_info


class TestQuadrantValidation:
    """Test quadrant framework validation."""

    @pytest.fixture
    def validator(self):
        """Create validation framework instance."""
        return ValidationFramework()

    def test_quadrant_consistency(self, validator):
        """Test quadrant definition consistency."""
        framework = QuadrantFramework()

        # Check that all quadrants have consistent structure
        for quadrant_id, quadrant_info in framework.quadrants.items():
            # Validate description length
            assert len(quadrant_info["description"]) > 50  # Substantial description

            # Validate examples
            examples = quadrant_info["examples"]
            assert "sensemaking_inbound" in examples
            assert "action_outbound" in examples

            # Validate examples are non-empty
            assert len(examples["sensemaking_inbound"]) > 10
            assert len(examples["action_outbound"]) > 10

    def test_processing_level_validation(self, validator):
        """Test processing level analysis validation."""
        framework = QuadrantFramework()

        test_cases = [("data", "cognitive"), ("metadata", "metacognitive")]

        for data_type, cognitive_level in test_cases:
            analysis = framework.analyze_processing_level(data_type, cognitive_level)

            # Check meta level calculation
            meta_analysis = analysis["meta_level"]
            expected_meta_data = 1 if data_type == "metadata" else 0
            expected_meta_cognitive = 1 if cognitive_level == "metacognitive" else 0

            assert meta_analysis["meta_data_level"] == expected_meta_data
            assert meta_analysis["meta_cognitive_level"] == expected_meta_cognitive
            assert (
                meta_analysis["overall_meta_level"]
                == expected_meta_data + expected_meta_cognitive
            )


class TestQuadrantIntegration:
    """Test quadrant framework integration with other components."""

    def test_quadrant_with_active_inference(self):
        """Test quadrant framework provides context for Active Inference."""
        from src.active_inference import demonstrate_active_inference_concepts

        # Quadrant framework should provide context for understanding AI concepts
        quadrant_demo = demonstrate_quadrant_framework()
        ai_concepts = demonstrate_active_inference_concepts()

        # Both should be able to coexist and provide complementary insights
        assert "framework_overview" in quadrant_demo
        assert "concepts" in ai_concepts

        # Quadrant framework should mention Active Inference
        quadrant_text = str(quadrant_demo).lower()
        assert "active inference" in quadrant_text

    def test_visualization_data_structure(self):
        """Test that visualization data has correct structure."""
        framework = QuadrantFramework()
        viz_data = framework.create_quadrant_matrix_visualization()

        # Check connections
        connections = viz_data["connections"]
        assert len(connections) == 4  # All valid transitions

        # Verify connection structure
        for conn in connections:
            assert "from" in conn
            assert "to" in conn
            assert conn["from"].startswith("Q")
            assert conn["to"].startswith("Q")

    def test_quadrant_naming_consistency(self):
        """Test quadrant naming consistency."""
        framework = QuadrantFramework()

        # Check that quadrant names follow consistent pattern
        for quadrant_id, quadrant_info in framework.quadrants.items():
            # ID should match coordinate pattern
            data_type, cog_level = quadrant_info["coordinates"]

            # Correct quadrant numbering: data+cognitive=Q1, metadata+cognitive=Q2,
            # data+metacognitive=Q3, metadata+metacognitive=Q4
            quadrant_num = 1
            if data_type == "metadata":
                quadrant_num += 1
            if cog_level == "metacognitive":
                quadrant_num += 2
            expected_prefix = f"Q{quadrant_num}"

            assert quadrant_id.startswith(expected_prefix)
            assert data_type in quadrant_id
            assert cog_level in quadrant_id


class TestQuadrantMathematicalProperties:
    """Test mathematical properties of quadrant framework."""

    def test_meta_level_progression(self):
        """Test meta-level progression is mathematically consistent."""
        framework = QuadrantFramework()

        # Meta-level should increase systematically
        meta_levels = []

        for data_type in ["data", "metadata"]:
            for cog_level in ["cognitive", "metacognitive"]:
                analysis = framework.analyze_processing_level(data_type, cog_level)
                meta_level = analysis["meta_level"]["overall_meta_level"]
                meta_levels.append((data_type, cog_level, meta_level))

        # Sort by meta level
        meta_levels.sort(key=lambda x: x[2])

        # Should progress from 0 to 2
        # Note: both (metadata, cognitive) and (data, metacognitive) have meta_level = 1
        # The actual ordering depends on the iteration order in the test
        expected_meta_levels = {
            ("data", "cognitive"): 0,
            ("metadata", "cognitive"): 1,
            ("data", "metacognitive"): 1,
            ("metadata", "metacognitive"): 2,
        }

        # Check that each combination has the correct meta level
        for data_type, cog_level, actual_meta_level in meta_levels:
            expected_meta_level = expected_meta_levels[(data_type, cog_level)]
            assert actual_meta_level == expected_meta_level

    def test_complexity_assessment(self):
        """Test complexity assessment is consistent."""
        framework = QuadrantFramework()

        complexities = {}

        for data_type in ["data", "metadata"]:
            for cog_level in ["cognitive", "metacognitive"]:
                analysis = framework.analyze_processing_level(data_type, cog_level)
                complexity = analysis["level_assessment"]["complexity"]
                complexities[f"{data_type}_{cog_level}"] = complexity

        # Complexity should increase with meta-level
        assert complexities["data_cognitive"] < complexities["metadata_cognitive"]
        assert complexities["metadata_cognitive"] < complexities["data_metacognitive"]
        assert (
            complexities["data_metacognitive"] < complexities["metadata_metacognitive"]
        )
