"""Tests for utils/exceptions.py module.

Comprehensive tests for the ValidationError exception class, ensuring all
initialization options and exception behavior are tested.
"""

import pytest
from src.utils.exceptions import ValidationError


class TestValidationError:
    """Test ValidationError exception functionality."""

    def test_initialization_message_only(self):
        """Test ValidationError initialization with message only."""
        error = ValidationError("Test error message")

        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.context == {}
        assert error.suggestions == []

    def test_initialization_with_context(self):
        """Test ValidationError initialization with context dictionary."""
        context = {
            "field": "probability_distribution",
            "value": [0.2, 0.3, 0.6],
            "expected_sum": 1.0,
        }
        error = ValidationError("Validation failed", context=context)

        assert str(error) == "Validation failed"
        assert error.message == "Validation failed"
        assert error.context == context
        assert error.suggestions == []

    def test_initialization_with_suggestions(self):
        """Test ValidationError initialization with suggestions list."""
        suggestions = [
            "Check that probabilities sum to 1.0",
            "Verify no negative values",
            "Ensure all values are finite",
        ]
        error = ValidationError("Validation failed", suggestions=suggestions)

        assert str(error) == "Validation failed"
        assert error.message == "Validation failed"
        assert error.context == {}
        assert error.suggestions == suggestions

    def test_initialization_with_context_and_suggestions(self):
        """Test ValidationError initialization with both context and suggestions."""
        context = {"field": "distribution", "sum": 1.1}
        suggestions = ["Normalize the distribution", "Check input values"]
        error = ValidationError(
            "Distribution validation failed", context=context, suggestions=suggestions
        )

        assert str(error) == "Distribution validation failed"
        assert error.context == context
        assert error.suggestions == suggestions

    def test_initialization_context_none(self):
        """Test ValidationError initialization with context=None (defaults to {})."""
        error = ValidationError("Test", context=None)

        assert error.context == {}

    def test_initialization_suggestions_none(self):
        """Test ValidationError initialization with suggestions=None (defaults to [])."""
        error = ValidationError("Test", suggestions=None)

        assert error.suggestions == []

    def test_raise_and_catch(self):
        """Test raising and catching ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Test error")

        assert str(exc_info.value) == "Test error"
        assert exc_info.value.message == "Test error"

    def test_raise_with_context(self):
        """Test raising ValidationError with context."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError(
                "Validation failed", context={"value": 1.1, "expected": 1.0}
            )

        assert exc_info.value.context == {"value": 1.1, "expected": 1.0}

    def test_raise_with_suggestions(self):
        """Test raising ValidationError with suggestions."""
        suggestions = ["Fix 1", "Fix 2"]
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Error", suggestions=suggestions)

        assert exc_info.value.suggestions == suggestions

    def test_exception_inheritance(self):
        """Test that ValidationError is a proper Exception."""
        error = ValidationError("Test")

        assert isinstance(error, Exception)
        assert isinstance(error, ValidationError)

    def test_exception_message_propagation(self):
        """Test that exception message propagates correctly."""
        error = ValidationError("Detailed error message")

        # Exception should be usable in string contexts
        assert "Detailed error message" in str(error)
        assert error.message in str(error)

    def test_context_access(self):
        """Test accessing context after exception creation."""
        context = {"key1": "value1", "key2": 42}
        error = ValidationError("Error", context=context)

        assert error.context["key1"] == "value1"
        assert error.context["key2"] == 42

    def test_suggestions_access(self):
        """Test accessing suggestions after exception creation."""
        suggestions = ["Suggestion 1", "Suggestion 2", "Suggestion 3"]
        error = ValidationError("Error", suggestions=suggestions)

        assert len(error.suggestions) == 3
        assert "Suggestion 1" in error.suggestions
        assert "Suggestion 2" in error.suggestions
        assert "Suggestion 3" in error.suggestions

    def test_complex_context(self):
        """Test ValidationError with complex context structure."""
        context = {
            "nested": {"level1": {"level2": "value"}},
            "list": [1, 2, 3],
            "number": 42.5,
        }
        error = ValidationError("Complex error", context=context)

        assert error.context["nested"]["level1"]["level2"] == "value"
        assert error.context["list"] == [1, 2, 3]
        assert error.context["number"] == 42.5

    def test_empty_suggestions_list(self):
        """Test ValidationError with empty suggestions list."""
        error = ValidationError("Error", suggestions=[])

        assert error.suggestions == []

    def test_empty_context_dict(self):
        """Test ValidationError with empty context dictionary."""
        error = ValidationError("Error", context={})

        assert error.context == {}

    def test_exception_chaining(self):
        """Test ValidationError can be chained with other exceptions."""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            error = ValidationError("Validation failed", context={"original": str(e)})

            assert isinstance(error, ValidationError)
            assert error.context["original"] == "Original error"

    def test_multiple_validation_errors(self):
        """Test creating multiple ValidationError instances."""
        error1 = ValidationError("Error 1", context={"id": 1})
        error2 = ValidationError("Error 2", context={"id": 2})
        error3 = ValidationError("Error 3", suggestions=["Fix"])

        assert error1.message == "Error 1"
        assert error2.message == "Error 2"
        assert error3.message == "Error 3"
        assert error1.context["id"] == 1
        assert error2.context["id"] == 2
        assert error3.suggestions == ["Fix"]


class TestBackwardCompatWrappers:
    """Test backward-compat wrapper modules in src/ root."""

    def test_active_inference_wrapper(self):
        """Test src/active_inference.py re-exports from core."""
        from src.active_inference import ActiveInferenceFramework
        assert ActiveInferenceFramework is not None

    def test_free_energy_principle_wrapper(self):
        """Test src/free_energy_principle.py re-exports from core."""
        from src.free_energy_principle import FreeEnergyPrinciple
        assert FreeEnergyPrinciple is not None

    def test_meta_cognition_wrapper(self):
        """Test src/meta_cognition.py re-exports from framework."""
        from src.meta_cognition import MetaCognitiveSystem
        assert MetaCognitiveSystem is not None

    def test_modeler_perspective_wrapper(self):
        """Test src/modeler_perspective.py re-exports from framework."""
        from src.modeler_perspective import ModelerPerspective
        assert ModelerPerspective is not None

    def test_validation_wrapper(self):
        """Test src/validation.py re-exports from analysis."""
        from src.validation import ValidationFramework
        assert ValidationFramework is not None

    def test_statistical_analysis_wrapper(self):
        """Test src/statistical_analysis.py re-exports from analysis."""
        from src.statistical_analysis import StatisticalAnalyzer
        assert StatisticalAnalyzer is not None
