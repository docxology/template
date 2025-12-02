"""Form Reduction Engine for Boundary Logic.

This module implements the reduction (simplification) of forms according to
Spencer-Brown's two fundamental axioms:

1. Calling (Involution): ⟨⟨a⟩⟩ = a
   - Double crossing returns to the original state
   - Equivalent to double negation elimination

2. Crossing (Condensation): ⟨ ⟩⟨ ⟩ = ⟨ ⟩
   - Two marks condense to one mark
   - The marked state is idempotent

The reduction engine provides:
- Step-by-step reduction traces
- Canonical form computation
- Proof verification
- Reduction complexity analysis
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.forms import Form, make_void, make_mark


class ReductionRule(Enum):
    """The fundamental reduction rules (axioms)."""
    CALLING = "calling"       # ⟨⟨a⟩⟩ → a (involution)
    CROSSING = "crossing"     # ⟨ ⟩⟨ ⟩ → ⟨ ⟩ (condensation)
    VOID_REMOVAL = "void"     # Remove void from juxtaposition
    FLATTEN = "flatten"       # Flatten unnecessary nesting


@dataclass
class ReductionStep:
    """A single step in a form reduction.
    
    Attributes:
        rule: The rule applied in this step
        before: Form before reduction
        after: Form after reduction
        location: Description of where the rule was applied
    """
    rule: ReductionRule
    before: Form
    after: Form
    location: str = ""
    
    def __str__(self) -> str:
        return f"{self.before} → {self.after} [{self.rule.value}]"


@dataclass
class ReductionTrace:
    """Complete trace of a form reduction to canonical form.
    
    Attributes:
        original: Starting form
        canonical: Final reduced form
        steps: List of reduction steps
        is_complete: Whether reduction reached canonical form
    """
    original: Form
    canonical: Form
    steps: List[ReductionStep] = field(default_factory=list)
    is_complete: bool = True
    
    @property
    def step_count(self) -> int:
        """Number of reduction steps."""
        return len(self.steps)
    
    def __str__(self) -> str:
        lines = [f"Reduction: {self.original} → {self.canonical}"]
        for i, step in enumerate(self.steps, 1):
            lines.append(f"  {i}. {step}")
        return "\n".join(lines)


class ReductionEngine:
    """Engine for reducing forms to canonical form.
    
    Implements the axioms of boundary logic to simplify
    forms to their irreducible canonical representations.
    """
    
    def __init__(self, max_iterations: int = 1000) -> None:
        """Initialize the reduction engine.
        
        Args:
            max_iterations: Maximum reduction steps before giving up
        """
        self.max_iterations = max_iterations
        self._stats: Dict[str, int] = {
            "calling_applications": 0,
            "crossing_applications": 0,
            "total_reductions": 0,
        }
    
    def reduce(self, form: Form) -> Form:
        """Reduce a form to canonical form.
        
        Args:
            form: Form to reduce
            
        Returns:
            Canonical (fully reduced) form
        """
        trace = self.reduce_with_trace(form)
        return trace.canonical
    
    def reduce_with_trace(self, form: Form) -> ReductionTrace:
        """Reduce a form and return the complete trace.
        
        Args:
            form: Form to reduce
            
        Returns:
            ReductionTrace with all steps
        """
        trace = ReductionTrace(original=form.copy(), canonical=form.copy())
        current = form.copy()
        
        for _ in range(self.max_iterations):
            step = self._reduce_once(current)
            if step is None:
                # No more reductions possible
                trace.canonical = current
                trace.is_complete = True
                return trace
            
            trace.steps.append(step)
            current = step.after.copy()
        
        # Hit max iterations
        trace.canonical = current
        trace.is_complete = False
        return trace
    
    def _reduce_once(self, form: Form) -> Optional[ReductionStep]:
        """Apply one reduction step if possible.
        
        Attempts rules in order: calling, crossing, void removal, flatten.
        
        Args:
            form: Form to reduce
            
        Returns:
            ReductionStep if a rule was applied, None otherwise
        """
        # Try calling (double enclosure)
        step = self._try_calling(form)
        if step:
            self._stats["calling_applications"] += 1
            return step
        
        # Try crossing (mark condensation)
        step = self._try_crossing(form)
        if step:
            self._stats["crossing_applications"] += 1
            return step
        
        # Try void removal
        step = self._try_void_removal(form)
        if step:
            return step
        
        # Try recursive reduction in contents
        step = self._try_recursive(form)
        if step:
            return step
        
        return None
    
    def _try_calling(self, form: Form) -> Optional[ReductionStep]:
        """Try to apply the calling axiom: ⟨⟨a⟩⟩ → a.
        
        The calling axiom states that double enclosure returns to the original.
        For ⟨⟨contents⟩⟩, the result is the contents of the inner mark.
        
        Cases:
        - ⟨⟨⟩⟩ (inner is simple mark): inner contains void → return void
        - ⟨⟨a⟩⟩ (inner has one content): return a
        - ⟨⟨a b ...⟩⟩ (inner has multiple): return juxtaposition a b ...
        
        Args:
            form: Form to check
            
        Returns:
            ReductionStep if calling was applied
        """
        if not form.is_marked:
            return None
        
        if len(form.contents) != 1:
            return None
        
        inner = form.contents[0]
        if not inner.is_marked:
            return None
        
        # Found ⟨⟨...⟩⟩ pattern - reduce based on inner contents
        if len(inner.contents) == 0:
            # ⟨⟨⟩⟩ = ⟨⟨void⟩⟩ = void (inner mark contains void)
            result = make_void()
        elif len(inner.contents) == 1:
            # ⟨⟨a⟩⟩ = a
            result = inner.contents[0].copy()
        else:
            # ⟨⟨a b ...⟩⟩ = a b ... (juxtaposition)
            result = Form(contents=[f.copy() for f in inner.contents], is_marked=False)
        
        return ReductionStep(
            rule=ReductionRule.CALLING,
            before=form,
            after=result,
            location="root"
        )
    
    def _try_crossing(self, form: Form) -> Optional[ReductionStep]:
        """Try to apply the crossing axiom: ⟨ ⟩⟨ ⟩ → ⟨ ⟩.
        
        This applies to juxtaposed marks at any level.
        
        Args:
            form: Form to check
            
        Returns:
            ReductionStep if crossing was applied
        """
        if form.is_marked and len(form.contents) == 0:
            # This IS a simple mark, nothing to reduce
            return None
        
        # Check for multiple simple marks in contents
        simple_marks = [f for f in form.contents if f.is_marked and len(f.contents) == 0]
        
        if len(simple_marks) >= 2:
            # Found ⟨ ⟩⟨ ⟩... pattern - condense to single ⟨ ⟩
            other_contents = [f for f in form.contents if not (f.is_marked and len(f.contents) == 0)]
            
            if not other_contents and not form.is_marked:
                # Pure juxtaposition of only marks -> single mark
                new_form = make_mark()
            else:
                # Mix of marks and other content
                new_contents = other_contents + [make_mark()]
                new_form = Form(contents=new_contents, is_marked=form.is_marked)
            
            return ReductionStep(
                rule=ReductionRule.CROSSING,
                before=form,
                after=new_form,
                location="contents"
            )
        
        return None
    
    def _try_void_removal(self, form: Form) -> Optional[ReductionStep]:
        """Try to apply void domination semantics.
        
        In boundary logic, void (FALSE) dominates in juxtaposition (AND):
        - Unmarked form with void: a AND FALSE = FALSE → entire form becomes void
        - Marked form with void: ⟨a AND FALSE⟩ = NOT(FALSE) = TRUE → mark
        
        This implements the logical truth that:
        - Any conjunction with FALSE is FALSE
        - Negation of FALSE is TRUE
        
        Args:
            form: Form to check
            
        Returns:
            ReductionStep if void domination was applied
        """
        if not form.contents:
            return None
        
        has_void = any(f.is_void() for f in form.contents)
        
        if not has_void:
            return None
        
        # Void domination semantics
        if form.is_marked:
            # ⟨... void ...⟩ = ⟨... AND FALSE⟩ = NOT(FALSE) = TRUE = mark
            new_form = make_mark()
        else:
            # ... void ... = ... AND FALSE = FALSE = void
            new_form = make_void()
        
        return ReductionStep(
            rule=ReductionRule.VOID_REMOVAL,
            before=form,
            after=new_form,
            location="contents"
        )
    
    def _try_recursive(self, form: Form) -> Optional[ReductionStep]:
        """Try to reduce within nested contents.
        
        Args:
            form: Form to check
            
        Returns:
            ReductionStep if any nested reduction was made
        """
        for i, subform in enumerate(form.contents):
            step = self._reduce_once(subform)
            if step:
                # Build new form with reduced subform
                new_contents = list(form.contents)
                new_contents[i] = step.after.copy()
                new_form = Form(contents=new_contents, is_marked=form.is_marked)
                
                return ReductionStep(
                    rule=step.rule,
                    before=form,
                    after=new_form,
                    location=f"contents[{i}]"
                )
        
        return None
    
    def is_canonical(self, form: Form) -> bool:
        """Check if a form is already in canonical form.
        
        Args:
            form: Form to check
            
        Returns:
            True if no further reductions are possible
        """
        return self._reduce_once(form) is None
    
    def are_equivalent(self, form1: Form, form2: Form) -> bool:
        """Check if two forms are equivalent (reduce to same canonical form).
        
        Args:
            form1: First form
            form2: Second form
            
        Returns:
            True if forms reduce to the same canonical form
        """
        canonical1 = self.reduce(form1)
        canonical2 = self.reduce(form2)
        return canonical1 == canonical2
    
    def get_stats(self) -> Dict[str, int]:
        """Get reduction statistics.
        
        Returns:
            Dictionary of reduction statistics
        """
        return self._stats.copy()
    
    def reset_stats(self) -> None:
        """Reset reduction statistics."""
        self._stats = {
            "calling_applications": 0,
            "crossing_applications": 0,
            "total_reductions": 0,
        }


def reduce_form(form: Form) -> Form:
    """Reduce a form to canonical form.
    
    Convenience function using default ReductionEngine.
    
    Args:
        form: Form to reduce
        
    Returns:
        Canonical form
    """
    engine = ReductionEngine()
    return engine.reduce(form)


def reduce_with_trace(form: Form) -> ReductionTrace:
    """Reduce a form and return the complete trace.
    
    Args:
        form: Form to reduce
        
    Returns:
        ReductionTrace with all steps
    """
    engine = ReductionEngine()
    return engine.reduce_with_trace(form)


def forms_equivalent(form1: Form, form2: Form) -> bool:
    """Check if two forms are equivalent.
    
    Two forms are equivalent if they reduce to the same canonical form.
    
    Args:
        form1: First form
        form2: Second form
        
    Returns:
        True if forms are equivalent
    """
    engine = ReductionEngine()
    return engine.are_equivalent(form1, form2)


def demonstrate_calling() -> ReductionTrace:
    """Demonstrate the calling axiom: ⟨⟨a⟩⟩ = a.
    
    Returns:
        ReductionTrace showing the axiom in action
    """
    # Create ⟨⟨⟨ ⟩⟩⟩ which should reduce to ⟨ ⟩
    inner_mark = make_mark()
    double_enclosed = Form.enclose(Form.enclose(inner_mark))
    
    return reduce_with_trace(double_enclosed)


def demonstrate_crossing() -> ReductionTrace:
    """Demonstrate the crossing axiom: ⟨ ⟩⟨ ⟩ = ⟨ ⟩.
    
    Returns:
        ReductionTrace showing the axiom in action
    """
    # Create ⟨ ⟩⟨ ⟩ (two marks juxtaposed)
    two_marks = Form.juxtapose(make_mark(), make_mark())
    
    return reduce_with_trace(two_marks)


def canonical_form(form: Form) -> Form:
    """Get the canonical (irreducible) form.
    
    This is the standard form that uniquely represents
    the equivalence class of the input form.
    
    Args:
        form: Input form
        
    Returns:
        Canonical form
    """
    return reduce_form(form)

