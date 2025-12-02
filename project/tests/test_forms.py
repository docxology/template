"""Tests for the forms module - core boundary logic structures.

Tests cover:
- Form construction (void, mark, enclosure, juxtaposition)
- Form properties (depth, size, predicates)
- String representation and parsing
- Boolean operators
"""
import pytest
from src.forms import (
    Form, FormType, make_void, make_mark, make_cross,
    enclose, juxtapose, negate, conjunction, disjunction,
    implication, equivalence, forms_equal, is_canonical
)


class TestFormConstruction:
    """Tests for form construction methods."""
    
    def test_make_void(self):
        """Test void form creation."""
        void = make_void()
        assert void.is_void()
        assert not void.is_marked
        assert len(void.contents) == 0
    
    def test_make_mark(self):
        """Test mark creation."""
        mark = make_mark()
        assert mark.is_simple_mark()
        assert mark.is_marked
        assert len(mark.contents) == 0
    
    def test_make_cross_alias(self):
        """Test that make_cross is alias for make_mark."""
        cross = make_cross()
        mark = make_mark()
        assert cross == mark
    
    def test_enclose_void(self):
        """Test enclosing void."""
        void = make_void()
        enclosed = enclose(void)
        assert enclosed.is_marked
        assert len(enclosed.contents) == 1
        assert enclosed.contents[0].is_void()
    
    def test_enclose_mark(self):
        """Test enclosing a mark."""
        mark = make_mark()
        enclosed = enclose(mark)
        assert enclosed.is_marked
        assert len(enclosed.contents) == 1
    
    def test_juxtapose_marks(self):
        """Test juxtaposing multiple marks."""
        m1 = make_mark()
        m2 = make_mark()
        juxta = juxtapose(m1, m2)
        assert not juxta.is_marked
        assert len(juxta.contents) == 2
    
    def test_nested_enclosure(self):
        """Test nested enclosures."""
        mark = make_mark()
        single = enclose(mark)
        double = enclose(single)
        assert double.depth() == 3  # mark(1) + single(1) + double(1)


class TestFormPredicates:
    """Tests for form predicate methods."""
    
    def test_is_void(self):
        """Test is_void predicate."""
        assert make_void().is_void()
        assert not make_mark().is_void()
        assert not enclose(make_void()).is_void()
    
    def test_is_simple_mark(self):
        """Test is_simple_mark predicate."""
        assert make_mark().is_simple_mark()
        assert not make_void().is_simple_mark()
        assert not enclose(make_mark()).is_simple_mark()
    
    def test_is_marked(self):
        """Test is_marked property."""
        assert make_mark().is_marked
        assert enclose(make_void()).is_marked
        assert not make_void().is_marked
        assert not juxtapose(make_mark(), make_mark()).is_marked


class TestFormMetrics:
    """Tests for form metric methods."""
    
    def test_void_depth(self):
        """Test depth of void."""
        assert make_void().depth() == 0
    
    def test_mark_depth(self):
        """Test depth of mark."""
        assert make_mark().depth() == 1
    
    def test_nested_depth(self):
        """Test depth of nested forms."""
        form = enclose(enclose(make_mark()))
        assert form.depth() == 3
    
    def test_void_size(self):
        """Test size of void."""
        assert make_void().size() == 0
    
    def test_mark_size(self):
        """Test size of mark."""
        assert make_mark().size() == 1
    
    def test_complex_size(self):
        """Test size of complex forms."""
        form = enclose(juxtapose(make_mark(), make_mark()))
        # 1 outer + 2 inner marks
        assert form.size() == 3


class TestFormEquality:
    """Tests for form equality."""
    
    def test_void_equality(self):
        """Test void equals void."""
        assert make_void() == make_void()
    
    def test_mark_equality(self):
        """Test mark equals mark."""
        assert make_mark() == make_mark()
    
    def test_void_not_equals_mark(self):
        """Test void does not equal mark."""
        assert make_void() != make_mark()
    
    def test_structural_equality(self):
        """Test structural equality of complex forms."""
        f1 = enclose(make_mark())
        f2 = enclose(make_mark())
        assert f1 == f2
    
    def test_forms_equal_function(self):
        """Test forms_equal function."""
        assert forms_equal(make_mark(), make_mark())
        assert not forms_equal(make_void(), make_mark())


class TestFormStringRepresentation:
    """Tests for form string representation."""
    
    def test_void_string(self):
        """Test void string representation."""
        void = make_void()
        assert str(void) == "∅"
    
    def test_mark_string(self):
        """Test mark string representation."""
        mark = make_mark()
        assert "⟨" in str(mark) or str(mark) == "⟨⟩"
    
    def test_to_string_styles(self):
        """Test different string styles."""
        mark = make_mark()
        assert "⟨" in mark.to_string("angle")
        assert "(" in mark.to_string("paren")
        assert "[" in mark.to_string("square")


class TestBooleanOperators:
    """Tests for Boolean operator forms."""
    
    def test_negate(self):
        """Test negation creates enclosure."""
        mark = make_mark()
        negated = negate(mark)
        assert negated.is_marked
        assert len(negated.contents) == 1
    
    def test_conjunction(self):
        """Test conjunction is juxtaposition."""
        a = make_mark()
        b = make_void()
        conj = conjunction(a, b)
        assert not conj.is_marked
        assert len(conj.contents) == 2
    
    def test_disjunction_structure(self):
        """Test disjunction creates De Morgan form."""
        a = make_mark()
        b = make_void()
        disj = disjunction(a, b)
        # Should be ⟨⟨a⟩⟨b⟩⟩
        assert disj.is_marked
    
    def test_implication_structure(self):
        """Test implication structure."""
        a = make_mark()
        b = make_void()
        impl = implication(a, b)
        # Should be ⟨a⟨b⟩⟩
        assert impl.is_marked


class TestFormCopy:
    """Tests for form copying."""
    
    def test_copy_void(self):
        """Test copying void."""
        void = make_void()
        copy = void.copy()
        assert copy == void
        assert copy is not void
    
    def test_copy_complex(self):
        """Test copying complex form."""
        form = enclose(juxtapose(make_mark(), make_void()))
        copy = form.copy()
        assert copy == form
        assert copy is not form
        assert copy.contents[0] is not form.contents[0]


class TestFormIteration:
    """Tests for form iteration."""
    
    def test_iter_subforms_void(self):
        """Test iterating subforms of void."""
        void = make_void()
        subforms = list(void.iter_subforms())
        assert len(subforms) == 1
    
    def test_iter_subforms_nested(self):
        """Test iterating nested subforms."""
        inner = make_mark()
        outer = enclose(inner)
        subforms = list(outer.iter_subforms())
        assert len(subforms) == 2


class TestIsCanonical:
    """Tests for canonical form checking."""
    
    def test_void_is_canonical(self):
        """Test void is canonical."""
        assert is_canonical(make_void())
    
    def test_mark_is_canonical(self):
        """Test mark is canonical."""
        assert is_canonical(make_mark())
    
    def test_double_enclosure_not_canonical(self):
        """Test double enclosure is not canonical."""
        form = enclose(enclose(make_mark()))
        assert not is_canonical(form)
    
    def test_multiple_marks_not_canonical(self):
        """Test multiple juxtaposed marks not canonical."""
        form = juxtapose(make_mark(), make_mark())
        assert not is_canonical(form)

