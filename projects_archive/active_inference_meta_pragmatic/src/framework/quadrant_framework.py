"""2x2 Quadrant Framework Implementation.

This module implements the 2x2 matrix framework that structures the analysis:
- X-axis: Data vs Meta-Data
- Y-axis: Cognitive vs Meta-Cognitive

The four quadrants represent different levels of processing and reasoning:

Quadrant 1 (Data, Cognitive): Basic data processing at primary cognitive level
Quadrant 2 (Meta-Data, Cognitive): Meta-data organization within cognitive processes
Quadrant 3 (Data, Meta-Cognitive): Reflective processing of data at meta-cognitive level
Quadrant 4 (Meta-Data, Meta-Cognitive): Higher-order reasoning involving meta-data and meta-cognition
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from numpy.typing import NDArray
from ..utils.exceptions import ValidationError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class QuadrantFramework:
    """Implementation of the 2x2 quadrant framework for Active Inference analysis.

    The framework organizes different levels of processing and reasoning into four quadrants,
    enabling systematic analysis of meta-pragmatic and meta-epistemic aspects.
    """

    def __init__(self) -> None:
        """Initialize the quadrant framework."""
        self.quadrants = self._define_quadrants()
        logger.info("Initialized 2x2 Quadrant Framework")

    def _define_quadrants(self) -> Dict[str, Dict[str, Union[str, Dict]]]:
        """Define the four quadrants of the framework.

        Returns:
            Dictionary containing quadrant definitions and characteristics
        """
        return {
            "Q1_data_cognitive": {
                "name": "Data Processing (Cognitive)",
                "coordinates": ("data", "cognitive"),
                "description": """
                Basic data processing at the primary cognitive level. This represents
                the foundation of cognitive processing where raw data is interpreted
                and acted upon at the fundamental level of cognition.
                """,
                "examples": {
                    "sensemaking_inbound": """
                    Raw sensory inputs interpreted through basic cognitive processes:
                    edge detection, scene recognition, pattern identification.
                    """,
                    "action_outbound": """
                    First-order homeostatic policy selection based on immediate needs:
                    thermostat maintaining temperature, basic reflex responses.
                    """,
                },
                "active_inference_role": "Baseline pragmatic and epistemic processing (EFE)",
                "mathematical_formulation": "Basic EFE = G(π) + H[Q(π)]",
            },
            "Q2_metadata_cognitive": {
                "name": "Meta-Data Organization (Cognitive)",
                "coordinates": ("metadata", "cognitive"),
                "description": """
                Meta-data organization within cognitive processes. This involves
                applying primary cognition to meta-data (information that shapes
                how data is processed), enabling more sophisticated information handling.
                """,
                "examples": {
                    "sensemaking_inbound": """
                    Adding time-stamps, quality scores, and confidence metrics to
                    incoming data during processing. Quality assessment and filtering.
                    """,
                    "action_outbound": """
                    Adding time-stamps and confidence scores to selected actions.
                    Action provenance and reliability tracking.
                    """,
                },
                "active_inference_role": "Enhanced epistemic processing with meta-data",
                "mathematical_formulation": "Extended EFE with meta-data weighting",
            },
            "Q3_data_metacognitive": {
                "name": "Reflective Processing (Meta-Cognitive)",
                "coordinates": ("data", "metacognitive"),
                "description": """
                Reflective processing of data at a meta-cognitive level. This represents
                'thinking about thinking' in relation to raw data, enabling evaluation
                of cognitive processes and adjustment of processing regimes.
                """,
                "examples": {
                    "sensemaking_inbound": """
                    Evaluating confidence in inferences, assessing processing accuracy,
                    adjusting attention allocation based on uncertainty levels.
                    """,
                    "action_outbound": """
                    Self-assessment of action effectiveness, adjustment of decision
                    thresholds, meta-control of behavioral strategies.
                    """,
                },
                "active_inference_role": "Meta-cognitive evaluation and control",
                "mathematical_formulation": "Hierarchical EFE with self-monitoring",
            },
            "Q4_metadata_metacognitive": {
                "name": "Higher-Order Reasoning (Meta-Cognitive)",
                "coordinates": ("metadata", "metacognitive"),
                "description": """
                Higher-order reasoning involving both meta-data and meta-cognitive processes.
                This operates on a meta-pragmatic and meta-epistemic level, processing
                meta-data about meta-cognition and enabling framework-level reasoning.
                """,
                "examples": {
                    "sensemaking_inbound": """
                    Processing meta-data about cognitive processes: analyzing patterns
                    in confidence levels, evaluating meta-cognitive strategies.
                    """,
                    "action_outbound": """
                    Framework-level control: selecting among different cognitive regimes,
                    adapting meta-cognitive strategies based on context.
                    """,
                },
                "active_inference_role": "Meta-pragmatic and meta-epistemic framework control",
                "mathematical_formulation": "Multi-level hierarchical EFE optimization",
            },
        }

    def get_quadrant(self, quadrant_id: str) -> Dict[str, Union[str, Dict]]:
        """Get detailed information about a specific quadrant.

        Args:
            quadrant_id: Quadrant identifier (Q1_data_cognitive, etc.)

        Returns:
            Dictionary containing quadrant details

        Raises:
            ValidationError: If quadrant_id is invalid
        """
        if quadrant_id not in self.quadrants:
            valid_ids = list(self.quadrants.keys())
            raise ValidationError(
                f"Invalid quadrant ID: {quadrant_id}. Valid IDs: {valid_ids}"
            )

        return self.quadrants[quadrant_id]

    def analyze_processing_level(
        self, data_type: str, cognitive_level: str
    ) -> Dict[str, Union[str, Dict]]:
        """Analyze processing characteristics for given data and cognitive levels.

        Args:
            data_type: 'data' or 'metadata'
            cognitive_level: 'cognitive' or 'metacognitive'

        Returns:
            Dictionary containing analysis results

        Raises:
            ValidationError: If parameters are invalid
        """
        if data_type not in ["data", "metadata"]:
            raise ValidationError(
                f"Invalid data_type: {data_type}. Must be 'data' or 'metadata'"
            )
        if cognitive_level not in ["cognitive", "metacognitive"]:
            raise ValidationError(
                f"Invalid cognitive_level: {cognitive_level}. Must be 'cognitive' or 'metacognitive'"
            )

        # Map to quadrant ID
        quadrant_num = 1
        if data_type == "metadata":
            quadrant_num += 1
        if cognitive_level == "metacognitive":
            quadrant_num += 2
        quadrant_id = f"Q{quadrant_num}_{data_type}_{cognitive_level}"

        quadrant_info = self.get_quadrant(quadrant_id)

        analysis = {
            "quadrant_id": quadrant_id,
            "processing_characteristics": quadrant_info,
            "level_assessment": self._assess_processing_level(
                data_type, cognitive_level
            ),
            "active_inference_implications": self._analyze_active_inference_implications(
                quadrant_id
            ),
            "meta_level": self._determine_meta_level(data_type, cognitive_level),
        }

        logger.info(
            f"Analyzed processing level: {data_type} × {cognitive_level} → {quadrant_id}"
        )
        return analysis

    def _assess_processing_level(
        self, data_type: str, cognitive_level: str
    ) -> Dict[str, Union[str, int]]:
        """Assess the processing level characteristics."""
        assessment = {
            "complexity": 1,
            "abstraction_level": 1,
            "meta_level": 0,
            "processing_characteristics": [],
        }

        if data_type == "metadata":
            assessment["complexity"] += 1
            assessment["abstraction_level"] += 1
            assessment["processing_characteristics"].append("meta-data processing")

        if cognitive_level == "metacognitive":
            assessment["complexity"] += 2
            assessment["abstraction_level"] += 2
            assessment["meta_level"] += 1
            assessment["processing_characteristics"].append("meta-cognitive evaluation")

        if data_type == "metadata" and cognitive_level == "metacognitive":
            assessment["complexity"] += 1
            assessment["meta_level"] += 1
            assessment["processing_characteristics"].append("higher-order reasoning")

        return assessment

    def _analyze_active_inference_implications(
        self, quadrant_id: str
    ) -> Dict[str, str]:
        """Analyze Active Inference implications for the quadrant."""
        implications = {
            "Q1_data_cognitive": {
                "pragmatic_aspect": "Direct action selection for immediate homeostasis",
                "epistemic_aspect": "Basic perception as inference",
                "meta_level": "Primary pragmatic and epistemic processing",
            },
            "Q2_metadata_cognitive": {
                "pragmatic_aspect": "Enhanced action selection with reliability tracking",
                "epistemic_aspect": "Meta-data guided perception and learning",
                "meta_level": "Enhanced epistemic processing",
            },
            "Q3_data_metacognitive": {
                "pragmatic_aspect": "Self-regulated action selection and control",
                "epistemic_aspect": "Confidence-based perception and attention",
                "meta_level": "Meta-cognitive evaluation and control",
            },
            "Q4_metadata_metacognitive": {
                "pragmatic_aspect": "Framework-level pragmatic specification",
                "epistemic_aspect": "Epistemic framework definition and adaptation",
                "meta_level": "Meta-pragmatic and meta-epistemic framework control",
            },
        }

        return implications.get(quadrant_id, {})

    def _determine_meta_level(
        self, data_type: str, cognitive_level: str
    ) -> Dict[str, Union[str, int]]:
        """Determine the meta-level characteristics."""
        meta_analysis = {
            "meta_data_level": 0,
            "meta_cognitive_level": 0,
            "overall_meta_level": 0,
            "classification": "primary",
        }

        if data_type == "metadata":
            meta_analysis["meta_data_level"] = 1
            meta_analysis["overall_meta_level"] += 1

        if cognitive_level == "metacognitive":
            meta_analysis["meta_cognitive_level"] = 1
            meta_analysis["overall_meta_level"] += 1

        if meta_analysis["overall_meta_level"] == 0:
            meta_analysis["classification"] = "primary processing"
        elif meta_analysis["overall_meta_level"] == 1:
            meta_analysis["classification"] = "meta-level processing"
        else:
            meta_analysis["classification"] = "higher-order reasoning"

        return meta_analysis

    def demonstrate_quadrant_transitions(self) -> Dict[str, List[Dict]]:
        """Demonstrate how processing can transition between quadrants.

        Returns:
            Dictionary containing transition examples and pathways
        """
        transitions = {
            "developmental_progression": [
                {
                    "from": "Q1_data_cognitive",
                    "to": "Q2_metadata_cognitive",
                    "description": "Adding meta-data tracking to basic processing",
                    "active_inference_mechanism": "Enhanced epistemic affordance",
                },
                {
                    "from": "Q2_metadata_cognitive",
                    "to": "Q3_data_metacognitive",
                    "description": "Adding self-evaluation to meta-data processing",
                    "active_inference_mechanism": "Meta-cognitive control",
                },
                {
                    "from": "Q3_data_metacognitive",
                    "to": "Q4_metadata_metacognitive",
                    "description": "Processing meta-data about meta-cognition",
                    "active_inference_mechanism": "Higher-order framework adaptation",
                },
            ],
            "situational_adaptation": [
                {
                    "trigger": "uncertainty_increase",
                    "transition": "Q1 → Q3 (increased meta-cognitive evaluation)",
                    "purpose": "Enhanced uncertainty monitoring",
                },
                {
                    "trigger": "complexity_increase",
                    "transition": "Q2 → Q4 (meta-data about meta-cognition)",
                    "purpose": "Framework-level adaptation",
                },
            ],
            "learning_progression": [
                {
                    "stage": "novice",
                    "dominant_quadrant": "Q1_data_cognitive",
                    "characteristics": "Rule-based processing, limited meta-awareness",
                },
                {
                    "stage": "competent",
                    "dominant_quadrant": "Q2_metadata_cognitive",
                    "characteristics": "Meta-data utilization, improved reliability",
                },
                {
                    "stage": "expert",
                    "dominant_quadrant": "Q3_data_metacognitive",
                    "characteristics": "Reflective practice, self-regulation",
                },
                {
                    "stage": "master",
                    "dominant_quadrant": "Q4_metadata_metacognitive",
                    "characteristics": "Framework mastery, creative adaptation",
                },
            ],
        }

        logger.info("Demonstrated quadrant transitions and processing progressions")
        return transitions

    def create_quadrant_matrix_visualization(self) -> Dict[str, Union[str, Dict]]:
        """Create data structure for quadrant matrix visualization.

        Returns:
            Dictionary containing visualization data for the 2x2 matrix
        """
        matrix_data = {
            "title": "Active Inference Meta-Pragmatic Framework",
            "subtitle": "2×2 Matrix: Data/Meta-Data × Cognitive/Meta-Cognitive",
            "x_axis": {
                "label": "Information Type",
                "categories": ["Data", "Meta-Data"],
                "description": "Raw data vs. information about data processing",
            },
            "y_axis": {
                "label": "Processing Level",
                "categories": ["Cognitive", "Meta-Cognitive"],
                "description": "Direct processing vs. processing about processing",
            },
            "quadrants": {
                "top_left": {
                    "id": "Q3",
                    "name": "Data & Meta-Cognitive",
                    "description": "Reflective Processing",
                    "color": "#FF6B6B",
                },
                "top_right": {
                    "id": "Q4",
                    "name": "Meta-Data & Meta-Cognitive",
                    "description": "Higher-Order Reasoning",
                    "color": "#4ECDC4",
                },
                "bottom_left": {
                    "id": "Q1",
                    "name": "Data & Cognitive",
                    "description": "Basic Processing",
                    "color": "#45B7D1",
                },
                "bottom_right": {
                    "id": "Q2",
                    "name": "Meta-Data & Cognitive",
                    "description": "Organization",
                    "color": "#FFA07A",
                },
            },
            "connections": [
                {"from": "Q1", "to": "Q2", "label": "Add Meta-Data"},
                {"from": "Q1", "to": "Q3", "label": "Add Reflection"},
                {"from": "Q2", "to": "Q4", "label": "Add Reflection"},
                {"from": "Q3", "to": "Q4", "label": "Add Meta-Data"},
            ],
        }

        logger.info("Created quadrant matrix visualization data structure")
        return matrix_data


def demonstrate_quadrant_framework() -> Dict[str, Union[str, Dict]]:
    """Demonstrate the complete quadrant framework.

    Returns:
        Dictionary containing framework demonstration and examples
    """
    framework = QuadrantFramework()

    # Get all quadrant definitions
    all_quadrants = {
        qid: framework.get_quadrant(qid) for qid in framework.quadrants.keys()
    }

    # Analyze specific processing levels
    level_analysis = {}
    for data_type in ["data", "metadata"]:
        for cog_level in ["cognitive", "metacognitive"]:
            level_analysis[f"{data_type}_{cog_level}"] = (
                framework.analyze_processing_level(data_type, cog_level)
            )

    # Demonstrate transitions
    transitions = framework.demonstrate_quadrant_transitions()

    # Create visualization data
    visualization = framework.create_quadrant_matrix_visualization()

    demonstration = {
        "framework_overview": """
        The 2×2 quadrant framework provides a systematic way to understand how Active Inference
        operates across different levels of abstraction, from basic data processing to higher-order
        reasoning about meta-cognitive processes. This framework reveals the meta-pragmatic and
        meta-epistemic nature of Active Inference as a modeling methodology.
        """,
        "quadrant_definitions": all_quadrants,
        "level_analysis": level_analysis,
        "transitions": transitions,
        "visualization_data": visualization,
        "key_insights": {
            "meta_pragmatic": """
            Active Inference is meta-pragmatic because it allows modelers to specify particular
            pragmatic considerations for modeled entities, enabling goal-directed behavior that
            balances information-seeking (epistemic) with reward-seeking (pragmatic) motivations.
            """,
            "meta_epistemic": """
            Active Inference is meta-epistemic because it enables modelers to define the very
            structure of how beliefs are formed and updated, specifying epistemic frameworks
            within which agents operate.
            """,
            "cognitive_security_implications": """
            This framework has implications for cognitive security: understanding how meta-level
            processing can be manipulated or defended against, and how higher-order reasoning
            affects vulnerability to misinformation or cognitive attacks.
            """,
        },
    }

    logger.info("Demonstrated complete quadrant framework with all components")
    return demonstration
