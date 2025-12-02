"""Boolean Algebra Isomorphism for Boundary Logic.

This module establishes the precise correspondence between boundary logic
(Laws of Form) and Boolean algebra, demonstrating that containment theory
provides an equivalent but fundamentally different notation for logic.

Key Correspondences:
    - ⟨ ⟩ (mark/cross) ↔ TRUE (1)
    - void (empty) ↔ FALSE (0)
    - ⟨a⟩ (enclosure) ↔ NOT a
    - ab (juxtaposition) ↔ a AND b
    - ⟨⟨a⟩⟨b⟩⟩ ↔ a OR b (De Morgan form)

The isomorphism demonstrates that boundary logic is not merely a notation
but a complete Boolean algebra with spatial/topological interpretation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from src.forms import Form, make_void, make_mark, enclose, juxtapose


class BooleanValue(Enum):
    """Boolean truth values."""
    FALSE = 0
    TRUE = 1
    
    def __bool__(self) -> bool:
        return self == BooleanValue.TRUE
    
    def __str__(self) -> str:
        return "T" if self == BooleanValue.TRUE else "F"


@dataclass
class BooleanExpression:
    """A Boolean expression that can be converted to/from boundary form.
    
    Attributes:
        operator: The Boolean operator (AND, OR, NOT, VAR, CONST)
        operands: Child expressions (for operators)
        value: Constant value (for CONST)
        variable: Variable name (for VAR)
    """
    operator: str
    operands: List[BooleanExpression] = None
    value: Optional[bool] = None
    variable: Optional[str] = None
    
    def __post_init__(self):
        if self.operands is None:
            self.operands = []
    
    @classmethod
    def const(cls, value: bool) -> BooleanExpression:
        """Create a constant TRUE or FALSE."""
        return cls(operator="CONST", value=value)
    
    @classmethod
    def var(cls, name: str) -> BooleanExpression:
        """Create a variable reference."""
        return cls(operator="VAR", variable=name)
    
    @classmethod
    def not_(cls, expr: BooleanExpression) -> BooleanExpression:
        """Create NOT expression."""
        return cls(operator="NOT", operands=[expr])
    
    @classmethod
    def and_(cls, *exprs: BooleanExpression) -> BooleanExpression:
        """Create AND expression."""
        return cls(operator="AND", operands=list(exprs))
    
    @classmethod
    def or_(cls, *exprs: BooleanExpression) -> BooleanExpression:
        """Create OR expression."""
        return cls(operator="OR", operands=list(exprs))
    
    @classmethod
    def implies(cls, a: BooleanExpression, b: BooleanExpression) -> BooleanExpression:
        """Create implication: a → b = NOT a OR b."""
        return cls.or_(cls.not_(a), b)
    
    @classmethod
    def iff(cls, a: BooleanExpression, b: BooleanExpression) -> BooleanExpression:
        """Create biconditional: a ↔ b."""
        return cls.and_(cls.implies(a, b), cls.implies(b, a))
    
    def __str__(self) -> str:
        if self.operator == "CONST":
            return "T" if self.value else "F"
        elif self.operator == "VAR":
            return self.variable
        elif self.operator == "NOT":
            return f"¬{self.operands[0]}"
        elif self.operator == "AND":
            return f"({' ∧ '.join(str(op) for op in self.operands)})"
        elif self.operator == "OR":
            return f"({' ∨ '.join(str(op) for op in self.operands)})"
        return f"{self.operator}({', '.join(str(op) for op in self.operands)})"


def boolean_to_form(expr: BooleanExpression) -> Form:
    """Convert a Boolean expression to boundary form.
    
    The translation follows these rules:
    - TRUE → ⟨ ⟩ (mark)
    - FALSE → void (empty)
    - NOT a → ⟨a⟩ (enclosure)
    - a AND b → ab (juxtaposition)
    - a OR b → ⟨⟨a⟩⟨b⟩⟩ (De Morgan)
    
    Args:
        expr: Boolean expression to convert
        
    Returns:
        Equivalent boundary form
    """
    if expr.operator == "CONST":
        return make_mark() if expr.value else make_void()
    
    elif expr.operator == "VAR":
        # Variables are represented as forms with metadata
        # For now, return a marked form as placeholder
        return make_mark()
    
    elif expr.operator == "NOT":
        inner = boolean_to_form(expr.operands[0])
        return enclose(inner)
    
    elif expr.operator == "AND":
        forms = [boolean_to_form(op) for op in expr.operands]
        return juxtapose(*forms)
    
    elif expr.operator == "OR":
        # a OR b = ⟨⟨a⟩⟨b⟩⟩ (De Morgan via boundary)
        forms = [enclose(boolean_to_form(op)) for op in expr.operands]
        return enclose(juxtapose(*forms))
    
    else:
        raise ValueError(f"Unknown operator: {expr.operator}")


def form_to_boolean(form: Form) -> bool:
    """Evaluate a ground boundary form to a Boolean value.
    
    Assumes the form contains no variables.
    
    The evaluation follows:
    - ⟨ ⟩ (mark) → TRUE
    - void (empty) → FALSE
    - ⟨a⟩ → NOT(eval(a))
    - ab → eval(a) AND eval(b)
    
    Args:
        form: Ground boundary form
        
    Returns:
        Boolean truth value
    """
    if form.is_void():
        return False
    
    if form.is_simple_mark():
        return True
    
    if form.is_marked:
        # Enclosure = NOT of contents
        if not form.contents:
            return True  # Empty mark is TRUE
        # Multiple contents are juxtaposed (AND), then negated
        inner_values = [form_to_boolean(f) for f in form.contents]
        return not all(inner_values)
    else:
        # Juxtaposition = AND
        if not form.contents:
            return False  # Empty unmarked is void = FALSE
        return all(form_to_boolean(f) for f in form.contents)


def evaluate_form(form: Form, assignment: Dict[str, bool] = None) -> bool:
    """Evaluate a boundary form with optional variable assignment.
    
    Args:
        form: Boundary form to evaluate
        assignment: Mapping of variable names to truth values
        
    Returns:
        Boolean truth value
    """
    # For ground forms, direct evaluation
    return form_to_boolean(form)


class BooleanAlgebra:
    """Boolean algebra operations with boundary form representation.
    
    Provides a complete Boolean algebra using boundary logic as
    the underlying representation.
    """
    
    @staticmethod
    def true_() -> Form:
        """The TRUE value as boundary form."""
        return make_mark()
    
    @staticmethod
    def false_() -> Form:
        """The FALSE value as boundary form."""
        return make_void()
    
    @staticmethod
    def not_(a: Form) -> Form:
        """Logical NOT: ⟨a⟩."""
        return enclose(a)
    
    @staticmethod
    def and_(*forms: Form) -> Form:
        """Logical AND: juxtaposition ab."""
        return juxtapose(*forms)
    
    @staticmethod
    def or_(*forms: Form) -> Form:
        """Logical OR: ⟨⟨a⟩⟨b⟩⟩."""
        negated = [enclose(f) for f in forms]
        return enclose(juxtapose(*negated))
    
    @staticmethod
    def nand(a: Form, b: Form) -> Form:
        """NAND gate: ⟨ab⟩."""
        return enclose(juxtapose(a, b))
    
    @staticmethod
    def nor(a: Form, b: Form) -> Form:
        """NOR gate: ⟨⟨⟨a⟩⟨b⟩⟩⟩ = ⟨a⟩⟨b⟩ (simplified)."""
        return juxtapose(enclose(a), enclose(b))
    
    @staticmethod
    def xor(a: Form, b: Form) -> Form:
        """XOR: (a AND NOT b) OR (NOT a AND b)."""
        return BooleanAlgebra.or_(
            BooleanAlgebra.and_(a, BooleanAlgebra.not_(b)),
            BooleanAlgebra.and_(BooleanAlgebra.not_(a), b)
        )
    
    @staticmethod
    def implies(a: Form, b: Form) -> Form:
        """Implication: a → b = ⟨a⟩ OR b = ⟨a⟨b⟩⟩."""
        return enclose(a, enclose(b))
    
    @staticmethod
    def iff(a: Form, b: Form) -> Form:
        """Biconditional: a ↔ b."""
        return BooleanAlgebra.and_(
            BooleanAlgebra.implies(a, b),
            BooleanAlgebra.implies(b, a)
        )


def verify_de_morgan_laws() -> Dict[str, bool]:
    """Verify De Morgan's laws in boundary logic.
    
    De Morgan's Laws:
    1. NOT(a AND b) = NOT a OR NOT b
    2. NOT(a OR b) = NOT a AND NOT b
    
    Returns:
        Dictionary with verification results
    """
    from src.reduction import forms_equivalent
    
    ba = BooleanAlgebra
    
    # Use mark as 'a' and void as 'b' for testing
    a = make_mark()
    b = make_void()
    
    # Law 1: NOT(a AND b) = NOT a OR NOT b
    lhs1 = ba.not_(ba.and_(a, b))
    rhs1 = ba.or_(ba.not_(a), ba.not_(b))
    law1 = forms_equivalent(lhs1, rhs1)
    
    # Law 2: NOT(a OR b) = NOT a AND NOT b
    lhs2 = ba.not_(ba.or_(a, b))
    rhs2 = ba.and_(ba.not_(a), ba.not_(b))
    law2 = forms_equivalent(lhs2, rhs2)
    
    return {
        "de_morgan_1": law1,
        "de_morgan_2": law2,
    }


def verify_boolean_axioms() -> Dict[str, bool]:
    """Verify Boolean algebra axioms in boundary form.
    
    Verifies:
    - Identity laws
    - Domination laws  
    - Idempotent laws
    - Complement laws
    - Double negation
    
    Returns:
        Dictionary with verification results
    """
    from src.reduction import forms_equivalent
    
    ba = BooleanAlgebra
    
    a = make_mark()  # Use mark as test variable
    true_ = ba.true_()
    false_ = ba.false_()
    
    results = {}
    
    # Identity: a AND TRUE = a
    results["and_identity"] = forms_equivalent(
        ba.and_(a, true_), a
    )
    
    # Identity: a OR FALSE = a
    results["or_identity"] = forms_equivalent(
        ba.or_(a, false_), a
    )
    
    # Domination: a AND FALSE = FALSE
    results["and_domination"] = forms_equivalent(
        ba.and_(a, false_), false_
    )
    
    # Domination: a OR TRUE = TRUE
    results["or_domination"] = forms_equivalent(
        ba.or_(a, true_), true_
    )
    
    # Idempotent: a AND a = a
    results["and_idempotent"] = forms_equivalent(
        ba.and_(a, a), a
    )
    
    # Idempotent: a OR a = a
    results["or_idempotent"] = forms_equivalent(
        ba.or_(a, a), a
    )
    
    # Complement: a AND NOT a = FALSE
    results["and_complement"] = forms_equivalent(
        ba.and_(a, ba.not_(a)), false_
    )
    
    # Double negation: NOT NOT a = a
    results["double_negation"] = forms_equivalent(
        ba.not_(ba.not_(a)), a
    )
    
    return results


def generate_truth_table(form: Form, variables: List[str] = None) -> List[Dict[str, Any]]:
    """Generate truth table for a boundary form.
    
    For ground forms (no variables), returns single evaluation.
    
    Args:
        form: Boundary form to evaluate
        variables: List of variable names (currently unused for ground forms)
        
    Returns:
        List of rows, each with inputs and output
    """
    # For ground forms
    result = form_to_boolean(form)
    return [{"form": str(form), "value": result}]


def is_tautology(form: Form) -> bool:
    """Check if a form is a tautology (always TRUE).
    
    In boundary logic, a tautology reduces to ⟨ ⟩.
    
    Args:
        form: Form to check
        
    Returns:
        True if form is a tautology
    """
    from src.reduction import reduce_form
    
    canonical = reduce_form(form)
    return canonical.is_simple_mark()


def is_contradiction(form: Form) -> bool:
    """Check if a form is a contradiction (always FALSE).
    
    In boundary logic, a contradiction reduces to void.
    
    Args:
        form: Form to check
        
    Returns:
        True if form is a contradiction
    """
    from src.reduction import reduce_form
    
    canonical = reduce_form(form)
    return canonical.is_void()


def is_satisfiable(form: Form) -> bool:
    """Check if a form is satisfiable (can be TRUE).
    
    Args:
        form: Form to check
        
    Returns:
        True if form can be satisfied
    """
    return not is_contradiction(form)

