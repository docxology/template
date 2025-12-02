"""Tests for Boolean algebra isomorphism.

Tests verify the correspondence between Boolean algebra
and boundary logic.
"""
import pytest
from src.forms import Form, make_void, make_mark, enclose, juxtapose
from src.algebra import (
    BooleanValue, BooleanExpression, BooleanAlgebra,
    boolean_to_form, form_to_boolean, evaluate_form,
    verify_de_morgan_laws, verify_boolean_axioms,
    is_tautology, is_contradiction, is_satisfiable
)


class TestBooleanValue:
    """Tests for BooleanValue enum."""
    
    def test_true_bool(self):
        """Test TRUE is truthy."""
        assert bool(BooleanValue.TRUE)
    
    def test_false_bool(self):
        """Test FALSE is falsy."""
        assert not bool(BooleanValue.FALSE)
    
    def test_str_representation(self):
        """Test string representation."""
        assert str(BooleanValue.TRUE) == "T"
        assert str(BooleanValue.FALSE) == "F"


class TestBooleanExpression:
    """Tests for BooleanExpression class."""
    
    def test_const_true(self):
        """Test constant TRUE."""
        expr = BooleanExpression.const(True)
        assert expr.operator == "CONST"
        assert expr.value == True
    
    def test_const_false(self):
        """Test constant FALSE."""
        expr = BooleanExpression.const(False)
        assert expr.operator == "CONST"
        assert expr.value == False
    
    def test_not_expression(self):
        """Test NOT expression."""
        expr = BooleanExpression.not_(BooleanExpression.const(True))
        assert expr.operator == "NOT"
    
    def test_and_expression(self):
        """Test AND expression."""
        expr = BooleanExpression.and_(
            BooleanExpression.const(True),
            BooleanExpression.const(False)
        )
        assert expr.operator == "AND"
        assert len(expr.operands) == 2
    
    def test_or_expression(self):
        """Test OR expression."""
        expr = BooleanExpression.or_(
            BooleanExpression.const(True),
            BooleanExpression.const(False)
        )
        assert expr.operator == "OR"


class TestBooleanAlgebra:
    """Tests for BooleanAlgebra class operations."""
    
    def test_true_is_mark(self):
        """Test TRUE is mark."""
        form = BooleanAlgebra.true_()
        assert form.is_simple_mark()
    
    def test_false_is_void(self):
        """Test FALSE is void."""
        form = BooleanAlgebra.false_()
        assert form.is_void()
    
    def test_not_operation(self):
        """Test NOT creates enclosure."""
        a = make_mark()
        result = BooleanAlgebra.not_(a)
        assert result.is_marked
        assert len(result.contents) == 1
    
    def test_and_operation(self):
        """Test AND is juxtaposition."""
        a = make_mark()
        b = make_void()
        result = BooleanAlgebra.and_(a, b)
        assert not result.is_marked
        assert len(result.contents) == 2
    
    def test_or_operation(self):
        """Test OR creates De Morgan form."""
        a = make_mark()
        b = make_void()
        result = BooleanAlgebra.or_(a, b)
        assert result.is_marked  # Outer enclosure
    
    def test_nand_operation(self):
        """Test NAND operation."""
        a = make_mark()
        b = make_mark()
        result = BooleanAlgebra.nand(a, b)
        assert result.is_marked


class TestBooleanToForm:
    """Tests for Boolean to form conversion."""
    
    def test_const_true(self):
        """Test TRUE converts to mark."""
        expr = BooleanExpression.const(True)
        form = boolean_to_form(expr)
        assert form.is_simple_mark()
    
    def test_const_false(self):
        """Test FALSE converts to void."""
        expr = BooleanExpression.const(False)
        form = boolean_to_form(expr)
        assert form.is_void()
    
    def test_not_conversion(self):
        """Test NOT converts to enclosure."""
        expr = BooleanExpression.not_(BooleanExpression.const(True))
        form = boolean_to_form(expr)
        assert form.is_marked


class TestFormToBoolean:
    """Tests for form to Boolean conversion."""
    
    def test_mark_is_true(self):
        """Test mark evaluates to TRUE."""
        assert form_to_boolean(make_mark()) == True
    
    def test_void_is_false(self):
        """Test void evaluates to FALSE."""
        assert form_to_boolean(make_void()) == False
    
    def test_enclosed_mark(self):
        """Test ⟨⟨ ⟩⟩ (NOT TRUE) is FALSE."""
        form = enclose(make_mark())
        assert form_to_boolean(form) == False
    
    def test_enclosed_void(self):
        """Test ⟨∅⟩ (NOT FALSE) is TRUE."""
        form = enclose(make_void())
        assert form_to_boolean(form) == True


class TestDeMorganLaws:
    """Tests for De Morgan's laws verification."""
    
    def test_de_morgan_verification(self):
        """Test De Morgan laws hold."""
        results = verify_de_morgan_laws()
        assert results["de_morgan_1"]
        assert results["de_morgan_2"]


class TestBooleanAxioms:
    """Tests for Boolean axiom verification."""
    
    def test_boolean_axioms(self):
        """Test Boolean axioms hold."""
        results = verify_boolean_axioms()
        # Check key axioms
        assert results["double_negation"]


class TestTautologyContradiction:
    """Tests for tautology and contradiction checking."""
    
    def test_mark_is_tautology(self):
        """Test mark is tautology."""
        assert is_tautology(make_mark())
    
    def test_void_is_contradiction(self):
        """Test void is contradiction."""
        assert is_contradiction(make_void())
    
    def test_void_not_satisfiable(self):
        """Test void is not satisfiable."""
        assert not is_satisfiable(make_void())
    
    def test_mark_is_satisfiable(self):
        """Test mark is satisfiable."""
        assert is_satisfiable(make_mark())
    
    def test_excluded_middle(self):
        """Test a ∨ ¬a is tautology."""
        # ⟨⟨a⟩a⟩ should be TRUE
        a = make_mark()
        form = enclose(juxtapose(enclose(a), a))
        assert is_tautology(form)

