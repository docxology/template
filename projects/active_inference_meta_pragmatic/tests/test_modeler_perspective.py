"""Tests for Modeler Perspective Implementation.

Comprehensive tests for modeler perspective including dual role, epistemic/pragmatic
specifications, self-reflective modeling, and meta-theoretical synthesis.
"""

import numpy as np
import pytest

from infrastructure.core.exceptions import ValidationError
from src.modeler_perspective import (
    ModelerPerspective,
    demonstrate_modeler_perspective
)
from src.validation import ValidationFramework


class TestModelerPerspective:
    """Test Modeler Perspective core functionality."""

    @pytest.fixture
    def modeler(self):
        """Create modeler perspective instance."""
        return ModelerPerspective()

    def test_initialization(self, modeler):
        """Test modeler perspective initialization."""
        assert modeler.specified_frameworks == {}
        assert modeler.self_reflective_insights == []

    def test_epistemic_framework_specification(self, modeler):
        """Test epistemic framework specification."""
        framework_name = "scientific_epistemology"
        epistemic_boundaries = {
            'observation_model': ['reliable_sensors', 'measurement_error'],
            'prior_knowledge': ['domain_expertise', 'initial_assumptions'],
            'learning_mechanisms': ['bayesian_inference', 'parameter_estimation']
        }

        framework = modeler.specify_epistemic_framework(
            framework_name, epistemic_boundaries
        )

        assert framework['framework_name'] == framework_name
        assert framework['epistemic_boundaries'] == epistemic_boundaries
        assert 'meta_epistemic_nature' in framework
        assert 'specification_power' in framework
        assert framework['framework_type'] == 'epistemic'

        # Should be stored in specified frameworks
        assert framework_name in modeler.specified_frameworks

    def test_pragmatic_framework_specification(self, modeler):
        """Test pragmatic framework specification."""
        framework_name = "goal_directed_behavior"
        pragmatic_considerations = {
            'primary_goals': ['information_seeking', 'resource_acquisition'],
            'value_tradeoffs': ['exploration_vs_exploitation', 'risk_vs_reward'],
            'decision_horizons': ['short_term', 'long_term', 'hierarchical']
        }

        framework = modeler.specify_pragmatic_framework(
            framework_name, pragmatic_considerations
        )

        assert framework['framework_name'] == framework_name
        assert framework['pragmatic_considerations'] == pragmatic_considerations
        assert 'meta_pragmatic_nature' in framework
        assert 'specification_power' in framework
        assert framework['framework_type'] == 'pragmatic'

        # Should be stored in specified frameworks
        assert framework_name in modeler.specified_frameworks

    def test_self_reflective_modeling(self, modeler):
        """Test self-reflective modeling analysis."""
        analysis = modeler.analyze_self_reflective_modeling()

        required_keys = [
            'dual_role_of_modeler',
            'self_understanding_through_modeling',
            'meta_theoretical_insights'
        ]

        for key in required_keys:
            assert key in analysis

        # Check dual role analysis
        dual_role = analysis['dual_role_of_modeler']
        assert 'architect_role' in dual_role
        assert 'subject_role' in dual_role
        assert 'recursive_modeling' in dual_role

        # Check self-understanding
        self_understanding = analysis['self_understanding_through_modeling']
        assert 'cognitive_self_modeling' in self_understanding
        assert 'epistemic_self_reflection' in self_understanding

    def test_meta_epistemic_modeling(self, modeler):
        """Test meta-epistemic modeling demonstration."""
        demonstration = modeler.demonstrate_meta_epistemic_modeling()

        required_keys = [
            'epistemic_framework_specification',
            'meta_epistemic_implications'
        ]

        for key in required_keys:
            assert key in demonstration

        # Check epistemic specification
        epistemic_spec = demonstration['epistemic_framework_specification']
        assert 'generative_model_design' in epistemic_spec
        assert 'observation_likelihoods_A' in epistemic_spec
        assert 'prior_beliefs_D' in epistemic_spec
        assert 'inference_structure' in epistemic_spec

    def test_meta_pragmatic_modeling(self, modeler):
        """Test meta-pragmatic modeling demonstration."""
        demonstration = modeler.demonstrate_meta_pragmatic_modeling()

        required_keys = [
            'pragmatic_framework_specification',
            'meta_pragmatic_implications'
        ]

        for key in required_keys:
            assert key in demonstration

        # Check pragmatic specification
        pragmatic_spec = demonstration['pragmatic_framework_specification']
        assert 'preference_structure_C' in pragmatic_spec
        assert 'goal_hierarchies' in pragmatic_spec
        assert 'expected_free_energy' in pragmatic_spec

    def test_modeler_specifications_demonstration(self, modeler):
        """Test modeler specifications demonstration."""
        demonstration = modeler.demonstrate_modeler_specifications()

        required_keys = [
            'epistemic_specifications',
            'pragmatic_specifications',
            'modeler_power_demonstration',
            'implications_for_cognitive_science'
        ]

        for key in required_keys:
            assert key in demonstration

        # Should have created specifications
        assert len(modeler.specified_frameworks) >= 2

    def test_meta_theoretical_synthesis(self, modeler):
        """Test meta-theoretical synthesis."""
        synthesis = modeler.synthesize_meta_theoretical_perspective()

        required_keys = [
            'core_thesis',
            'quadrant_analysis',
            'modeler_dual_role',
            'cognitive_security_implications',
            'free_energy_principle_integration'
        ]

        for key in required_keys:
            assert key in synthesis

        # Check core thesis
        assert 'meta-pragmatic and meta-epistemic' in synthesis['core_thesis']

        # Check quadrant analysis
        quadrant_analysis = synthesis['quadrant_analysis']
        expected_quadrant_keys = [
            'quadrant_1_basis',
            'quadrant_2_enhancement',
            'quadrant_3_reflection',
            'quadrant_4_higher_reasoning'
        ]
        for key in expected_quadrant_keys:
            assert key in quadrant_analysis

    def test_error_handling(self, modeler):
        """Test error handling for invalid inputs."""
        # Invalid framework name
        with pytest.raises((ValueError, KeyError, ValidationError)):
            modeler.specify_epistemic_framework("", {})

        # Empty specifications
        with pytest.raises((ValueError, KeyError, ValidationError)):
            modeler.specify_pragmatic_framework("test", {})


class TestModelerPerspectiveDemonstration:
    """Test modeler perspective comprehensive demonstration."""

    def test_demonstrate_modeler_perspective(self):
        """Test complete modeler perspective demonstration."""
        demonstration = demonstrate_modeler_perspective()

        required_keys = [
            'modeler_specifications',
            'meta_epistemic_demonstration',
            'meta_pragmatic_demonstration',
            'self_reflective_analysis',
            'meta_theoretical_synthesis',
            'key_insights'
        ]

        for key in required_keys:
            assert key in demonstration

        # Check key insights
        key_insights = demonstration['key_insights']
        required_insights = [
            'meta_epistemic_power',
            'meta_pragmatic_power',
            'recursive_self_understanding',
            'unified_cognitive_framework'
        ]

        for insight in required_insights:
            assert insight in key_insights

    def test_framework_storage(self):
        """Test framework storage and retrieval."""
        modeler = ModelerPerspective()

        # Specify frameworks
        epistemic = modeler.specify_epistemic_framework(
            'test_epistemic',
            {'test': 'epistemic_spec'}
        )

        pragmatic = modeler.specify_pragmatic_framework(
            'test_pragmatic',
            {'test': 'pragmatic_spec'}
        )

        # Check storage
        assert len(modeler.specified_frameworks) == 2
        assert 'test_epistemic' in modeler.specified_frameworks
        assert 'test_pragmatic' in modeler.specified_frameworks

        # Check framework types
        assert modeler.specified_frameworks['test_epistemic']['framework_type'] == 'epistemic'
        assert modeler.specified_frameworks['test_pragmatic']['framework_type'] == 'pragmatic'


class TestModelerValidation:
    """Test modeler perspective validation."""

    @pytest.fixture
    def validator(self):
        """Create validation framework instance."""
        return ValidationFramework()

    def test_framework_specification_validation(self, validator):
        """Test framework specification validation."""
        modeler = ModelerPerspective()

        # Specify valid frameworks
        epistemic = modeler.specify_epistemic_framework(
            'validation_test_epistemic',
            {
                'observation_model': ['sensors'],
                'prior_knowledge': ['expertise'],
                'learning_mechanisms': ['bayesian']
            }
        )

        pragmatic = modeler.specify_pragmatic_framework(
            'validation_test_pragmatic',
            {
                'primary_goals': ['information'],
                'value_tradeoffs': ['exploration'],
                'decision_horizons': ['short_term']
            }
        )

        # Validate specifications are reasonable
        assert len(epistemic['epistemic_boundaries']) > 0
        assert len(pragmatic['pragmatic_considerations']) > 0

        # Check meta-level descriptions
        assert 'meta-epistemic' in epistemic['meta_epistemic_nature'].lower()
        assert 'complex value structures' in pragmatic['meta_pragmatic_nature'].lower()

    def test_self_reflective_insights_tracking(self, validator):
        """Test self-reflective insights tracking."""
        modeler = ModelerPerspective()

        # Perform self-reflective analysis
        analysis = modeler.analyze_self_reflective_modeling()

        # Should store insights
        assert len(modeler.self_reflective_insights) > 0

        insight = modeler.self_reflective_insights[0]
        assert 'analysis' in insight
        assert 'insights' in insight

        # Insights should be meaningful
        assert len(insight['insights']) > 0
        for insight_text in insight['insights']:
            assert len(insight_text) > 10  # Substantial insights


class TestModelerIntegration:
    """Test modeler perspective integration with other components."""

    def test_modeler_with_generative_models(self):
        """Test modeler perspective with generative models."""
        from src.generative_models import create_simple_generative_model

        modeler = ModelerPerspective()
        gen_model = create_simple_generative_model()

        # Modeler should be able to specify frameworks that work with generative models
        epistemic_spec = modeler.specify_epistemic_framework(
            'generative_model_epistemology',
            {
                'matrix_A': 'observation likelihoods',
                'matrix_D': 'prior beliefs',
                'inference': 'bayesian updating'
            }
        )

        pragmatic_spec = modeler.specify_pragmatic_framework(
            'generative_model_pragmatics',
            {
                'matrix_C': 'preference structure',
                'efe': 'expected free energy',
                'policy_selection': 'efe minimization'
            }
        )

        # Should work together
        assert epistemic_spec['framework_type'] == 'epistemic'
        assert pragmatic_spec['framework_type'] == 'pragmatic'

        # Generative model should support these specifications
        assert gen_model.A is not None  # Epistemic (A matrix)
        assert gen_model.C is not None  # Pragmatic (C matrix)

    def test_modeler_with_quadrant_framework(self):
        """Test modeler perspective with quadrant framework."""
        from src.quadrant_framework import QuadrantFramework

        modeler = ModelerPerspective()
        quadrants = QuadrantFramework()

        # Modeler specifications should align with quadrant analysis
        epistemic_spec = modeler.specify_epistemic_framework(
            'quadrant_epistemology',
            {
                'data_processing': 'Q1 basic epistemic',
                'meta_data_processing': 'Q2 enhanced epistemic',
                'meta_cognitive_epistemic': 'Q4 meta-epistemic'
            }
        )

        pragmatic_spec = modeler.specify_pragmatic_framework(
            'quadrant_pragmatics',
            {
                'data_processing': 'Q1 basic pragmatic',
                'meta_cognitive_pragmatic': 'Q3 reflective pragmatic',
                'meta_data_pragmatic': 'Q4 meta-pragmatic'
            }
        )

        # Should be consistent with quadrant framework
        q4_info = quadrants.get_quadrant('Q4_metadata_metacognitive')
        assert 'meta-epistemic' in q4_info['description'].lower() or 'meta-pragmatic' in q4_info['description'].lower()

    def test_recursive_modeling_concept(self):
        """Test recursive modeling concept implementation."""
        modeler = ModelerPerspective()

        # The modeler modeling themselves using Active Inference
        self_reflection = modeler.analyze_self_reflective_modeling()

        dual_role = self_reflection['dual_role_of_modeler']

        # Should demonstrate recursive nature
        assert 'recursive' in dual_role['recursive_modeling'].lower()

        # Should show modeling others reveals self-insights
        self_understanding = self_reflection['self_understanding_through_modeling']
        assert 'modeling artificial agents' in self_understanding['cognitive_self_modeling'].lower()


class TestMetaTheoreticalSynthesis:
    """Test meta-theoretical synthesis."""

    def test_core_thesis_validation(self):
        """Test core thesis validation."""
        modeler = ModelerPerspective()
        synthesis = modeler.synthesize_meta_theoretical_perspective()

        core_thesis = synthesis['core_thesis']

        # Should contain key elements
        key_elements = [
            'meta-pragmatic',
            'meta-epistemic',
            'tradition of action and inquiry',
            'expected free energy'
        ]

        thesis_text = core_thesis.lower()
        for element in key_elements:
            assert element in thesis_text

    def test_quadrant_integration(self):
        """Test quadrant integration in synthesis."""
        modeler = ModelerPerspective()
        synthesis = modeler.synthesize_meta_theoretical_perspective()

        quadrant_analysis = synthesis['quadrant_analysis']

        # Should cover all quadrants
        expected_quadrant_keys = [
            'quadrant_1_basis',
            'quadrant_2_enhancement',
            'quadrant_3_reflection',
            'quadrant_4_higher_reasoning'
        ]
        for key in expected_quadrant_keys:
            assert key in quadrant_analysis

        # Q4 should mention meta-epistemic/meta-pragmatic
        q4_analysis = quadrant_analysis['quadrant_4_higher_reasoning']
        q4_text = q4_analysis.lower()
        assert 'framework-level' in q4_text and 'cognition itself' in q4_text

    def test_cognitive_security_implications(self):
        """Test cognitive security implications."""
        modeler = ModelerPerspective()
        synthesis = modeler.synthesize_meta_theoretical_perspective()

        security_implications = synthesis['cognitive_security_implications']

        required_implications = [
            'meta_cognitive_vulnerability',
            'epistemic_framework_manipulation',
            'pragmatic_framework_protection'
        ]

        for implication in required_implications:
            assert implication in security_implications

    def test_fep_integration(self):
        """Test Free Energy Principle integration."""
        modeler = ModelerPerspective()
        synthesis = modeler.synthesize_meta_theoretical_perspective()

        fep_integration = synthesis['free_energy_principle_integration']

        required_elements = [
            'unified_thing_definition',
            'bridge_physics_cognition',
            'structure_preservation'
        ]

        for element in required_elements:
            assert element in fep_integration


class TestModelerEdgeCases:
    """Test edge cases in modeler perspective."""

    def test_minimal_specifications(self):
        """Test minimal framework specifications."""
        modeler = ModelerPerspective()

        # Minimal but valid specifications
        epistemic = modeler.specify_epistemic_framework(
            'minimal_epistemic',
            {'basic': 'epistemic_spec'}
        )

        pragmatic = modeler.specify_pragmatic_framework(
            'minimal_pragmatic',
            {'basic': 'pragmatic_spec'}
        )

        assert epistemic['framework_type'] == 'epistemic'
        assert pragmatic['framework_type'] == 'pragmatic'

    def test_specification_overwrite(self):
        """Test framework specification overwrite."""
        modeler = ModelerPerspective()

        # Specify framework
        modeler.specify_epistemic_framework(
            'test_framework',
            {'version': '1'}
        )

        # Overwrite with new specification
        updated = modeler.specify_epistemic_framework(
            'test_framework',
            {'version': '2'}
        )

        # Should be updated
        assert modeler.specified_frameworks['test_framework']['epistemic_boundaries']['version'] == '2'

    def test_empty_modeler_analysis(self):
        """Test analysis with no prior specifications."""
        modeler = ModelerPerspective()

        # Should work even with no prior specifications
        analysis = modeler.analyze_self_reflective_modeling()
        assert 'dual_role_of_modeler' in analysis

        synthesis = modeler.synthesize_meta_theoretical_perspective()
        assert 'core_thesis' in synthesis