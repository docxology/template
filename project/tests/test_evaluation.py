"""Tests for form evaluation and semantic analysis.

Tests cover:
- Basic form evaluation
- Evaluation traces
- Semantic analysis
"""
import pytest
from src.forms import Form, make_void, make_mark, enclose, juxtapose
from src.evaluation import (
    EvaluationResult, EvaluationContext, FormEvaluator,
    evaluate, evaluate_with_trace, truth_value,
    is_true, is_false, analyze_form, SemanticAnalysis,
    count_true, count_false, partition_by_truth
)


class TestBasicEvaluation:
    """Tests for basic form evaluation."""
    
    def test_void_evaluates_false(self):
        """Test void evaluates to FALSE."""
        assert evaluate(make_void()) == False
    
    def test_mark_evaluates_true(self):
        """Test mark evaluates to TRUE."""
        assert evaluate(make_mark()) == True
    
    def test_enclosed_mark_is_false(self):
        """Test ⟨⟨ ⟩⟩ (NOT TRUE) is FALSE."""
        form = enclose(make_mark())
        assert evaluate(form) == False
    
    def test_enclosed_void_is_true(self):
        """Test ⟨∅⟩ (NOT FALSE) is TRUE."""
        form = enclose(make_void())
        assert evaluate(form) == True
    
    def test_juxtaposed_marks(self):
        """Test juxtaposed marks (AND) evaluation."""
        form = juxtapose(make_mark(), make_mark())
        assert evaluate(form) == True
    
    def test_juxtaposed_mark_void(self):
        """Test TRUE AND FALSE = FALSE."""
        form = juxtapose(make_mark(), make_void())
        assert evaluate(form) == False


class TestFormEvaluator:
    """Tests for FormEvaluator class."""
    
    def test_evaluator_creation(self):
        """Test evaluator creation."""
        evaluator = FormEvaluator()
        assert evaluator.context is not None
    
    def test_evaluator_with_context(self):
        """Test evaluator with custom context."""
        context = EvaluationContext(trace=True)
        evaluator = FormEvaluator(context)
        assert evaluator.context.trace == True
    
    def test_evaluate_with_result(self):
        """Test evaluate_with_result method."""
        evaluator = FormEvaluator()
        result = evaluator.evaluate_with_result(make_mark())
        assert result == EvaluationResult.TRUE
    
    def test_get_trace(self):
        """Test trace retrieval."""
        context = EvaluationContext(trace=True)
        evaluator = FormEvaluator(context)
        evaluator.evaluate(enclose(make_mark()))
        trace = evaluator.get_trace()
        assert len(trace) > 0


class TestEvaluationWithTrace:
    """Tests for traced evaluation."""
    
    def test_trace_returned(self):
        """Test trace is returned."""
        value, trace = evaluate_with_trace(make_mark())
        assert value == True
        assert isinstance(trace, list)
    
    def test_trace_has_steps(self):
        """Test trace contains evaluation steps."""
        form = enclose(enclose(make_mark()))
        value, trace = evaluate_with_trace(form)
        assert len(trace) > 0


class TestTruthValue:
    """Tests for truth_value function."""
    
    def test_truth_value_true(self):
        """Test truth_value returns 'TRUE'."""
        assert truth_value(make_mark()) == "TRUE"
    
    def test_truth_value_false(self):
        """Test truth_value returns 'FALSE'."""
        assert truth_value(make_void()) == "FALSE"


class TestPredicates:
    """Tests for is_true and is_false predicates."""
    
    def test_is_true_mark(self):
        """Test is_true for mark."""
        assert is_true(make_mark())
    
    def test_is_true_void(self):
        """Test is_true for void."""
        assert not is_true(make_void())
    
    def test_is_false_void(self):
        """Test is_false for void."""
        assert is_false(make_void())
    
    def test_is_false_mark(self):
        """Test is_false for mark."""
        assert not is_false(make_mark())


class TestSemanticAnalysis:
    """Tests for semantic analysis."""
    
    def test_analyze_mark(self):
        """Test analysis of mark."""
        analysis = analyze_form(make_mark())
        assert analysis.truth_value == True
        assert analysis.is_tautology == True
        assert analysis.is_contradiction == False
    
    def test_analyze_void(self):
        """Test analysis of void."""
        analysis = analyze_form(make_void())
        assert analysis.truth_value == False
        assert analysis.is_contradiction == True
        assert analysis.is_tautology == False
    
    def test_analysis_includes_metrics(self):
        """Test analysis includes all metrics."""
        form = enclose(make_mark())
        analysis = analyze_form(form)
        assert analysis.depth >= 1
        assert analysis.size >= 1


class TestBatchEvaluation:
    """Tests for batch evaluation functions."""
    
    def test_count_true(self):
        """Test counting TRUE forms."""
        forms = [make_mark(), make_void(), make_mark()]
        assert count_true(forms) == 2
    
    def test_count_false(self):
        """Test counting FALSE forms."""
        forms = [make_mark(), make_void(), make_void()]
        assert count_false(forms) == 2
    
    def test_partition_by_truth(self):
        """Test partitioning forms by truth value."""
        forms = [make_mark(), make_void(), make_mark(), make_void()]
        true_forms, false_forms = partition_by_truth(forms)
        assert len(true_forms) == 2
        assert len(false_forms) == 2


class TestComplexEvaluations:
    """Tests for complex form evaluations."""
    
    def test_double_negation(self):
        """Test ⟨⟨⟨ ⟩⟩⟩ = FALSE (NOT NOT TRUE = TRUE, wait...)."""
        # ⟨⟨⟨ ⟩⟩⟩ = ⟨⟨mark⟩⟩ = NOT NOT TRUE = TRUE after reduction
        # But evaluation before reduction:
        # ⟨⟨⟨ ⟩⟩⟩ = NOT(⟨⟨ ⟩⟩) = NOT(NOT(⟨ ⟩)) = NOT(NOT(TRUE)) = NOT(FALSE) = TRUE
        form = enclose(enclose(make_mark()))
        assert evaluate(form) == True
    
    def test_de_morgan_or(self):
        """Test De Morgan OR form ⟨⟨a⟩⟨b⟩⟩."""
        a = make_mark()  # TRUE
        b = make_void()  # FALSE
        # OR(TRUE, FALSE) = TRUE
        form = enclose(juxtapose(enclose(a), enclose(b)))
        assert evaluate(form) == True
    
    def test_nested_and(self):
        """Test nested AND (juxtaposition)."""
        # TRUE AND TRUE AND TRUE
        form = juxtapose(make_mark(), make_mark(), make_mark())
        assert evaluate(form) == True
        
        # TRUE AND FALSE AND TRUE
        form = juxtapose(make_mark(), make_void(), make_mark())
        assert evaluate(form) == False

