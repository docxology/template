"""Theorem Definitions and Proof Structures for Boundary Logic.

This module defines the fundamental theorems of the calculus of indications
(Laws of Form) and provides structures for representing and verifying proofs.

The theorem system builds upon the two axioms:
    1. Calling (J1): ⟨⟨a⟩⟩ = a
    2. Crossing (J2): ⟨ ⟩⟨ ⟩ = ⟨ ⟩

From these axioms, all theorems of Boolean algebra can be derived.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.forms import Form, make_void, make_mark, enclose, juxtapose
from src.reduction import reduce_form, forms_equivalent, ReductionTrace


class TheoremStatus(Enum):
    """Status of a theorem."""
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    FAILED = "failed"


@dataclass
class Theorem:
    """A theorem in boundary logic.
    
    A theorem asserts the equivalence of two forms under reduction.
    
    Attributes:
        name: Human-readable theorem name
        description: Explanation of the theorem
        lhs: Left-hand side form
        rhs: Right-hand side form
        status: Verification status
        proof_trace: Reduction traces showing equivalence
    """
    name: str
    description: str
    lhs: Form
    rhs: Form
    status: TheoremStatus = TheoremStatus.UNVERIFIED
    proof_trace: Optional[Tuple[ReductionTrace, ReductionTrace]] = None
    
    def verify(self) -> bool:
        """Verify the theorem by reducing both sides.
        
        Returns:
            True if lhs and rhs reduce to the same form
        """
        from src.reduction import reduce_with_trace
        
        lhs_trace = reduce_with_trace(self.lhs)
        rhs_trace = reduce_with_trace(self.rhs)
        
        equivalent = lhs_trace.canonical == rhs_trace.canonical
        
        self.status = TheoremStatus.VERIFIED if equivalent else TheoremStatus.FAILED
        self.proof_trace = (lhs_trace, rhs_trace)
        
        return equivalent
    
    def __str__(self) -> str:
        status_symbol = {
            TheoremStatus.UNVERIFIED: "?",
            TheoremStatus.VERIFIED: "✓",
            TheoremStatus.FAILED: "✗",
        }[self.status]
        return f"[{status_symbol}] {self.name}: {self.lhs} = {self.rhs}"


@dataclass 
class ProofStep:
    """A single step in a formal proof.
    
    Attributes:
        step_number: Position in proof
        form: Current form
        justification: Axiom or theorem applied
        from_step: Reference to previous step
    """
    step_number: int
    form: Form
    justification: str
    from_step: Optional[int] = None
    
    def __str__(self) -> str:
        ref = f" (from {self.from_step})" if self.from_step else ""
        return f"{self.step_number}. {self.form} [{self.justification}{ref}]"


@dataclass
class Proof:
    """A formal proof of a theorem.
    
    Attributes:
        theorem: The theorem being proved
        steps: Sequence of proof steps
        is_complete: Whether proof reaches conclusion
    """
    theorem: Theorem
    steps: List[ProofStep] = field(default_factory=list)
    is_complete: bool = False
    
    def add_step(self, form: Form, justification: str, from_step: int = None) -> None:
        """Add a step to the proof.
        
        Args:
            form: Form at this step
            justification: Axiom/theorem name
            from_step: Previous step reference
        """
        step = ProofStep(
            step_number=len(self.steps) + 1,
            form=form,
            justification=justification,
            from_step=from_step
        )
        self.steps.append(step)
    
    def check_complete(self) -> bool:
        """Check if the proof reaches the theorem's RHS.
        
        Returns:
            True if last step matches RHS
        """
        if not self.steps:
            return False
        
        last_form = self.steps[-1].form
        self.is_complete = forms_equivalent(last_form, self.theorem.rhs)
        return self.is_complete
    
    def __str__(self) -> str:
        lines = [f"Proof of: {self.theorem.name}"]
        lines.append(f"Goal: {self.theorem.lhs} = {self.theorem.rhs}")
        lines.append("-" * 40)
        for step in self.steps:
            lines.append(str(step))
        status = "QED" if self.is_complete else "INCOMPLETE"
        lines.append(f"\n[{status}]")
        return "\n".join(lines)


# =============================================================================
# Fundamental Axioms (as theorems for reference)
# =============================================================================

def axiom_calling() -> Theorem:
    """Axiom J1 (Calling): ⟨⟨a⟩⟩ = a.
    
    The law of calling (involution): crossing twice returns.
    """
    a = make_mark()
    lhs = enclose(enclose(a))
    rhs = a
    
    return Theorem(
        name="J1 (Calling)",
        description="Double crossing returns to original: ⟨⟨a⟩⟩ = a",
        lhs=lhs,
        rhs=rhs
    )


def axiom_crossing() -> Theorem:
    """Axiom J2 (Crossing): ⟨ ⟩⟨ ⟩ = ⟨ ⟩.
    
    The law of crossing (condensation): marks condense.
    """
    lhs = juxtapose(make_mark(), make_mark())
    rhs = make_mark()
    
    return Theorem(
        name="J2 (Crossing)",
        description="Multiple marks condense: ⟨ ⟩⟨ ⟩ = ⟨ ⟩",
        lhs=lhs,
        rhs=rhs
    )


# =============================================================================
# Derived Theorems (Consequences)
# =============================================================================

def theorem_position() -> Theorem:
    """Theorem C1 (Position): ⟨⟨a⟩b⟩a = a.
    
    From the position of a form, its occurrence is determined.
    """
    a = make_mark()
    b = make_void()
    
    # ⟨⟨a⟩b⟩a - with b as void, this simplifies
    inner = enclose(a)  # ⟨a⟩
    enclosed = enclose(juxtapose(inner, b))  # ⟨⟨a⟩b⟩
    lhs = juxtapose(enclosed, a)  # ⟨⟨a⟩b⟩a
    rhs = a
    
    return Theorem(
        name="C1 (Position)",
        description="Position determines occurrence: ⟨⟨a⟩b⟩a = a",
        lhs=lhs,
        rhs=rhs
    )


def theorem_transposition() -> Theorem:
    """Theorem C2 (Transposition): ⟨⟨a⟩⟨b⟩⟩c = ⟨ac⟩⟨bc⟩.
    
    Distribution of enclosure (related to De Morgan).
    """
    a = make_mark()
    b = make_void()
    c = make_mark()
    
    # LHS: ⟨⟨a⟩⟨b⟩⟩c
    inner = juxtapose(enclose(a), enclose(b))
    lhs = juxtapose(enclose(inner), c)
    
    # RHS: ⟨ac⟩⟨bc⟩
    rhs = juxtapose(enclose(juxtapose(a, c)), enclose(juxtapose(b, c)))
    
    return Theorem(
        name="C2 (Transposition)",
        description="Transposition law: ⟨⟨a⟩⟨b⟩⟩c = ⟨ac⟩⟨bc⟩",
        lhs=lhs,
        rhs=rhs
    )


def theorem_generation() -> Theorem:
    """Theorem C3 (Generation): ⟨⟨a⟩a⟩ = ⟨ ⟩.
    
    A form with its negation generates the marked state.
    This corresponds to a ∨ ¬a = TRUE.
    """
    a = make_mark()
    
    # ⟨⟨a⟩a⟩
    lhs = enclose(juxtapose(enclose(a), a))
    rhs = make_mark()
    
    return Theorem(
        name="C3 (Generation)",
        description="Form with negation: ⟨⟨a⟩a⟩ = ⟨ ⟩ (excluded middle)",
        lhs=lhs,
        rhs=rhs
    )


def theorem_integration() -> Theorem:
    """Theorem C4 (Integration): ⟨ ⟩a = ⟨ ⟩.
    
    The mark dominates in juxtaposition under enclosure.
    This corresponds to TRUE ∨ a = TRUE.
    """
    a = make_void()  # Use void for distinct form
    
    # ⟨ ⟩a with enclosure
    lhs = enclose(juxtapose(make_mark(), a))
    # Actually: if ⟨ ⟩a is juxtaposed, within enclosure it's ⟨⟨ ⟩a⟩
    # Let's do the simpler form: just ⟨ ⟩a
    lhs = juxtapose(make_mark(), a)
    rhs = make_mark()
    
    return Theorem(
        name="C4 (Integration)",
        description="Mark dominates: ⟨ ⟩a = ⟨ ⟩",
        lhs=lhs,
        rhs=rhs
    )


def theorem_occultation() -> Theorem:
    """Theorem C5 (Occultation): ⟨⟨a⟩⟩a = a.
    
    Double negation with original form.
    """
    a = make_mark()
    
    # ⟨⟨a⟩⟩a
    lhs = juxtapose(enclose(enclose(a)), a)
    rhs = a
    
    return Theorem(
        name="C5 (Occultation)",
        description="Double negation with self: ⟨⟨a⟩⟩a = a",
        lhs=lhs,
        rhs=rhs
    )


def theorem_iteration() -> Theorem:
    """Theorem C6 (Iteration): aa = a.
    
    Idempotence of juxtaposition (forms with themselves).
    """
    a = make_mark()
    
    lhs = juxtapose(a, a)
    rhs = a
    
    return Theorem(
        name="C6 (Iteration)",
        description="Idempotence: aa = a",
        lhs=lhs,
        rhs=rhs
    )


def theorem_extension() -> Theorem:
    """Theorem C7 (Extension): ⟨⟨a⟩⟨b⟩⟩⟨⟨a⟩b⟩ = a.
    
    Extended form theorem.
    """
    a = make_mark()
    b = make_void()
    
    # ⟨⟨a⟩⟨b⟩⟩
    first = enclose(juxtapose(enclose(a), enclose(b)))
    # ⟨⟨a⟩b⟩
    second = enclose(juxtapose(enclose(a), b))
    
    lhs = juxtapose(first, second)
    rhs = a
    
    return Theorem(
        name="C7 (Extension)",
        description="Extension theorem: ⟨⟨a⟩⟨b⟩⟩⟨⟨a⟩b⟩ = a",
        lhs=lhs,
        rhs=rhs
    )


def theorem_echelon() -> Theorem:
    """Theorem C8 (Echelon): ⟨⟨ab⟩c⟩ = ⟨a c⟩⟨b c⟩.
    
    Echelon (cascade) theorem.
    """
    a = make_mark()
    b = make_void()
    c = make_mark()
    
    # ⟨⟨ab⟩c⟩
    lhs = enclose(juxtapose(enclose(juxtapose(a, b)), c))
    
    # ⟨a c⟩⟨b c⟩
    rhs = juxtapose(enclose(juxtapose(a, c)), enclose(juxtapose(b, c)))
    
    return Theorem(
        name="C8 (Echelon)",
        description="Echelon theorem: ⟨⟨ab⟩c⟩ = ⟨ac⟩⟨bc⟩",
        lhs=lhs,
        rhs=rhs
    )


def theorem_crosstransposition() -> Theorem:
    """Theorem C9 (Cross-transposition): ⟨⟨a c⟩⟨b c⟩⟩ = ⟨⟨a⟩⟨b⟩⟩c.
    
    Cross-transposition theorem.
    """
    a = make_mark()
    b = make_void()
    c = make_mark()
    
    # ⟨⟨ac⟩⟨bc⟩⟩
    lhs = enclose(juxtapose(
        enclose(juxtapose(a, c)),
        enclose(juxtapose(b, c))
    ))
    
    # ⟨⟨a⟩⟨b⟩⟩c
    rhs = juxtapose(enclose(juxtapose(enclose(a), enclose(b))), c)
    
    return Theorem(
        name="C9 (Cross-transposition)",
        description="Cross-transposition: ⟨⟨ac⟩⟨bc⟩⟩ = ⟨⟨a⟩⟨b⟩⟩c",
        lhs=lhs,
        rhs=rhs
    )


# =============================================================================
# Theorem Collection
# =============================================================================

def get_all_axioms() -> List[Theorem]:
    """Get all axioms of boundary logic.
    
    Returns:
        List of axiom theorems
    """
    return [
        axiom_calling(),
        axiom_crossing(),
    ]


def get_all_consequences() -> List[Theorem]:
    """Get all derived theorems (consequences).
    
    Returns:
        List of consequence theorems
    """
    return [
        theorem_position(),
        theorem_transposition(),
        theorem_generation(),
        theorem_integration(),
        theorem_occultation(),
        theorem_iteration(),
        theorem_extension(),
        theorem_echelon(),
        theorem_crosstransposition(),
    ]


def get_all_theorems() -> List[Theorem]:
    """Get all theorems (axioms and consequences).
    
    Returns:
        Complete list of theorems
    """
    return get_all_axioms() + get_all_consequences()


def verify_all_theorems() -> Dict[str, bool]:
    """Verify all theorems in the system.
    
    Returns:
        Dictionary mapping theorem names to verification results
    """
    results = {}
    for theorem in get_all_theorems():
        results[theorem.name] = theorem.verify()
    return results


def theorem_summary() -> str:
    """Generate a summary of all theorems and their status.
    
    Returns:
        Formatted summary string
    """
    lines = ["=" * 60]
    lines.append("BOUNDARY LOGIC THEOREM SUMMARY")
    lines.append("=" * 60)
    lines.append("")
    
    lines.append("AXIOMS (Primitive)")
    lines.append("-" * 40)
    for theorem in get_all_axioms():
        theorem.verify()
        lines.append(str(theorem))
    
    lines.append("")
    lines.append("CONSEQUENCES (Derived)")
    lines.append("-" * 40)
    for theorem in get_all_consequences():
        theorem.verify()
        lines.append(str(theorem))
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)

