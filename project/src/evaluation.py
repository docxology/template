"""Form Evaluation and Truth Value Extraction.

This module provides evaluation capabilities for boundary forms,
computing their Boolean truth values and analyzing their logical
properties.

Evaluation follows the fundamental correspondence:
    - ⟨ ⟩ (mark) → TRUE
    - void (empty) → FALSE
    - ⟨a⟩ → NOT(eval(a))
    - ab (juxtaposition) → eval(a) AND eval(b)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from src.forms import Form, make_void, make_mark


class EvaluationResult(Enum):
    """Possible evaluation results."""
    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"  # For forms with unbound variables
    
    def __bool__(self) -> bool:
        return self == EvaluationResult.TRUE
    
    def to_bool(self) -> Optional[bool]:
        """Convert to Python bool or None."""
        if self == EvaluationResult.TRUE:
            return True
        elif self == EvaluationResult.FALSE:
            return False
        return None


@dataclass
class EvaluationContext:
    """Context for evaluating forms with variables.
    
    Attributes:
        bindings: Variable name to truth value mappings
        trace: Whether to record evaluation trace
        steps: Recorded evaluation steps (if trace=True)
    """
    bindings: Dict[str, bool] = None
    trace: bool = False
    steps: List[str] = None
    
    def __post_init__(self):
        if self.bindings is None:
            self.bindings = {}
        if self.steps is None:
            self.steps = []
    
    def bind(self, name: str, value: bool) -> None:
        """Bind a variable to a truth value."""
        self.bindings[name] = value
    
    def lookup(self, name: str) -> Optional[bool]:
        """Look up a variable binding."""
        return self.bindings.get(name)
    
    def log(self, message: str) -> None:
        """Log an evaluation step."""
        if self.trace:
            self.steps.append(message)


class FormEvaluator:
    """Evaluator for boundary forms.
    
    Computes the Boolean truth value of forms following
    the Laws of Form semantics.
    """
    
    def __init__(self, context: EvaluationContext = None) -> None:
        """Initialize evaluator.
        
        Args:
            context: Evaluation context (created if not provided)
        """
        self.context = context or EvaluationContext()
    
    def evaluate(self, form: Form) -> bool:
        """Evaluate a form to its Boolean truth value.
        
        Args:
            form: Form to evaluate
            
        Returns:
            Boolean truth value
        """
        self.context.log(f"Evaluating: {form}")
        
        # Void is FALSE
        if form.is_void():
            self.context.log("  → void = FALSE")
            return False
        
        # Simple mark is TRUE
        if form.is_simple_mark():
            self.context.log("  → mark = TRUE")
            return True
        
        # Evaluate contents
        if form.is_marked:
            # Enclosure: NOT of contents
            return self._evaluate_enclosure(form)
        else:
            # Juxtaposition: AND of contents
            return self._evaluate_juxtaposition(form)
    
    def _evaluate_enclosure(self, form: Form) -> bool:
        """Evaluate an enclosed form: ⟨contents⟩ = NOT(contents).
        
        Args:
            form: Enclosed form
            
        Returns:
            Boolean truth value
        """
        if not form.contents:
            # Empty enclosure is TRUE
            self.context.log("  → ⟨ ⟩ = TRUE")
            return True
        
        # Evaluate inner contents as conjunction
        inner_value = self._evaluate_contents_as_and(form.contents)
        result = not inner_value
        
        self.context.log(f"  → ⟨{inner_value}⟩ = {result}")
        return result
    
    def _evaluate_juxtaposition(self, form: Form) -> bool:
        """Evaluate juxtaposed forms: a b = a AND b.
        
        Args:
            form: Form with juxtaposed contents
            
        Returns:
            Boolean truth value
        """
        if not form.contents:
            # Empty juxtaposition is void = FALSE
            self.context.log("  → void = FALSE")
            return False
        
        return self._evaluate_contents_as_and(form.contents)
    
    def _evaluate_contents_as_and(self, contents: List[Form]) -> bool:
        """Evaluate a list of forms as conjunction.
        
        Args:
            contents: List of forms
            
        Returns:
            AND of all form values
        """
        for f in contents:
            if not self.evaluate(f):
                return False
        return True
    
    def evaluate_with_result(self, form: Form) -> EvaluationResult:
        """Evaluate and return an EvaluationResult.
        
        Args:
            form: Form to evaluate
            
        Returns:
            EvaluationResult enum value
        """
        value = self.evaluate(form)
        return EvaluationResult.TRUE if value else EvaluationResult.FALSE
    
    def get_trace(self) -> List[str]:
        """Get the evaluation trace.
        
        Returns:
            List of evaluation steps
        """
        return self.context.steps.copy()


def evaluate(form: Form) -> bool:
    """Evaluate a form to its Boolean truth value.
    
    Convenience function for simple evaluation.
    
    Args:
        form: Form to evaluate
        
    Returns:
        Boolean truth value
    """
    evaluator = FormEvaluator()
    return evaluator.evaluate(form)


def evaluate_with_trace(form: Form) -> Tuple[bool, List[str]]:
    """Evaluate a form and return the evaluation trace.
    
    Args:
        form: Form to evaluate
        
    Returns:
        Tuple of (truth value, list of steps)
    """
    context = EvaluationContext(trace=True)
    evaluator = FormEvaluator(context)
    value = evaluator.evaluate(form)
    return value, evaluator.get_trace()


def truth_value(form: Form) -> str:
    """Get the truth value of a form as a string.
    
    Args:
        form: Form to evaluate
        
    Returns:
        "TRUE" or "FALSE"
    """
    return "TRUE" if evaluate(form) else "FALSE"


def is_true(form: Form) -> bool:
    """Check if a form evaluates to TRUE.
    
    Args:
        form: Form to check
        
    Returns:
        True if form is TRUE
    """
    return evaluate(form)


def is_false(form: Form) -> bool:
    """Check if a form evaluates to FALSE.
    
    Args:
        form: Form to check
        
    Returns:
        True if form is FALSE
    """
    return not evaluate(form)


@dataclass
class SemanticAnalysis:
    """Semantic analysis results for a form.
    
    Attributes:
        form: The analyzed form
        truth_value: Boolean truth value
        depth: Nesting depth
        size: Total mark count
        is_tautology: Whether always TRUE
        is_contradiction: Whether always FALSE
    """
    form: Form
    truth_value: bool
    depth: int
    size: int
    is_tautology: bool
    is_contradiction: bool
    
    def __str__(self) -> str:
        return (
            f"SemanticAnalysis(\n"
            f"  form={self.form},\n"
            f"  value={self.truth_value},\n"
            f"  depth={self.depth},\n"
            f"  size={self.size},\n"
            f"  tautology={self.is_tautology},\n"
            f"  contradiction={self.is_contradiction}\n"
            f")"
        )


def analyze_form(form: Form) -> SemanticAnalysis:
    """Perform semantic analysis on a form.
    
    Args:
        form: Form to analyze
        
    Returns:
        SemanticAnalysis with complete analysis
    """
    from src.reduction import reduce_form
    
    truth_value = evaluate(form)
    depth = form.depth()
    size = form.size()
    
    # Check canonical form for tautology/contradiction
    canonical = reduce_form(form)
    is_tautology = canonical.is_simple_mark()
    is_contradiction = canonical.is_void()
    
    return SemanticAnalysis(
        form=form,
        truth_value=truth_value,
        depth=depth,
        size=size,
        is_tautology=is_tautology,
        is_contradiction=is_contradiction
    )


def compare_evaluations(form1: Form, form2: Form) -> Dict[str, Any]:
    """Compare evaluations of two forms.
    
    Args:
        form1: First form
        form2: Second form
        
    Returns:
        Dictionary with comparison results
    """
    val1 = evaluate(form1)
    val2 = evaluate(form2)
    
    return {
        "form1": str(form1),
        "form2": str(form2),
        "value1": val1,
        "value2": val2,
        "equivalent": val1 == val2,
        "both_true": val1 and val2,
        "both_false": not val1 and not val2,
    }


def evaluate_all(forms: List[Form]) -> List[bool]:
    """Evaluate a list of forms.
    
    Args:
        forms: List of forms to evaluate
        
    Returns:
        List of truth values
    """
    return [evaluate(f) for f in forms]


def count_true(forms: List[Form]) -> int:
    """Count forms that evaluate to TRUE.
    
    Args:
        forms: List of forms
        
    Returns:
        Count of TRUE forms
    """
    return sum(1 for f in forms if evaluate(f))


def count_false(forms: List[Form]) -> int:
    """Count forms that evaluate to FALSE.
    
    Args:
        forms: List of forms
        
    Returns:
        Count of FALSE forms
    """
    return sum(1 for f in forms if not evaluate(f))


def partition_by_truth(forms: List[Form]) -> Tuple[List[Form], List[Form]]:
    """Partition forms into TRUE and FALSE groups.
    
    Args:
        forms: List of forms
        
    Returns:
        Tuple of (true_forms, false_forms)
    """
    true_forms = []
    false_forms = []
    
    for f in forms:
        if evaluate(f):
            true_forms.append(f)
        else:
            false_forms.append(f)
    
    return true_forms, false_forms

