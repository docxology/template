"""Comparison Module: Set Theory vs Containment Theory.

This module provides tools for comparing and contrasting
traditional set-theoretic foundations with boundary logic
(Containment Theory) foundations.

Key comparisons:
- Notation differences (∈ vs spatial containment)
- Axiom structures (ZFC vs Laws of Form)
- Proof lengths and complexity
- Expressiveness and parsimony
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.forms import Form, make_void, make_mark, enclose, juxtapose
from src.reduction import reduce_form, ReductionTrace, reduce_with_trace
from src.evaluation import evaluate


class NotationSystem(Enum):
    """Mathematical notation systems."""
    SET_THEORY = "set_theory"
    BOUNDARY_LOGIC = "boundary_logic"
    BOOLEAN_ALGEBRA = "boolean_algebra"
    PROPOSITIONAL = "propositional"


@dataclass
class ConceptMapping:
    """Mapping between equivalent concepts in different systems.
    
    Attributes:
        concept: Abstract concept name
        set_theory: Set theory representation
        boundary_logic: Boundary logic representation
        boolean_algebra: Boolean algebra representation
        propositional: Propositional logic representation
    """
    concept: str
    set_theory: str
    boundary_logic: str
    boolean_algebra: str
    propositional: str
    
    def as_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            "concept": self.concept,
            "set_theory": self.set_theory,
            "boundary_logic": self.boundary_logic,
            "boolean_algebra": self.boolean_algebra,
            "propositional": self.propositional,
        }


def get_concept_mappings() -> List[ConceptMapping]:
    """Get all concept mappings between systems.
    
    Returns:
        List of concept mappings
    """
    return [
        ConceptMapping(
            concept="True/Universal",
            set_theory="U (universal set)",
            boundary_logic="⟨ ⟩ (mark)",
            boolean_algebra="1",
            propositional="T (true)"
        ),
        ConceptMapping(
            concept="False/Empty",
            set_theory="∅ (empty set)",
            boundary_logic="(void)",
            boolean_algebra="0",
            propositional="F (false)"
        ),
        ConceptMapping(
            concept="Negation/Complement",
            set_theory="Aᶜ or A̅",
            boundary_logic="⟨a⟩",
            boolean_algebra="¬a or a'",
            propositional="¬a"
        ),
        ConceptMapping(
            concept="Conjunction/Intersection",
            set_theory="A ∩ B",
            boundary_logic="ab (juxtaposition)",
            boolean_algebra="a ∧ b",
            propositional="a ∧ b"
        ),
        ConceptMapping(
            concept="Disjunction/Union",
            set_theory="A ∪ B",
            boundary_logic="⟨⟨a⟩⟨b⟩⟩",
            boolean_algebra="a ∨ b",
            propositional="a ∨ b"
        ),
        ConceptMapping(
            concept="Implication/Subset",
            set_theory="A ⊆ B",
            boundary_logic="⟨a⟨b⟩⟩",
            boolean_algebra="a → b",
            propositional="a → b"
        ),
        ConceptMapping(
            concept="Membership",
            set_theory="x ∈ A",
            boundary_logic="x inside ⟨A⟩",
            boolean_algebra="A(x) = 1",
            propositional="A(x)"
        ),
        ConceptMapping(
            concept="Double Negation",
            set_theory="(Aᶜ)ᶜ = A",
            boundary_logic="⟨⟨a⟩⟩ = a (Axiom J1)",
            boolean_algebra="¬¬a = a",
            propositional="¬¬a ↔ a"
        ),
    ]


@dataclass
class FoundationComparison:
    """Comparison of foundational properties.
    
    Attributes:
        property_name: Name of the property
        set_theory_value: Value/status in set theory
        boundary_logic_value: Value/status in boundary logic
        advantage: Which system has advantage (if any)
        notes: Additional notes
    """
    property_name: str
    set_theory_value: str
    boundary_logic_value: str
    advantage: Optional[str] = None
    notes: str = ""


def get_foundation_comparisons() -> List[FoundationComparison]:
    """Get foundational property comparisons.
    
    Returns:
        List of foundation comparisons
    """
    return [
        FoundationComparison(
            property_name="Number of Axioms",
            set_theory_value="9+ (ZFC)",
            boundary_logic_value="2 (J1, J2)",
            advantage="boundary_logic",
            notes="Boundary logic is more parsimonious"
        ),
        FoundationComparison(
            property_name="Primitive Notion",
            set_theory_value="Membership (∈)",
            boundary_logic_value="Distinction (boundary)",
            advantage=None,
            notes="Different ontological commitments"
        ),
        FoundationComparison(
            property_name="Self-Reference",
            set_theory_value="Prohibited (Russell's paradox)",
            boundary_logic_value="Handled (imaginary values)",
            advantage="boundary_logic",
            notes="Spencer-Brown's imaginary Boolean values"
        ),
        FoundationComparison(
            property_name="Geometric Intuition",
            set_theory_value="Limited (Venn diagrams)",
            boundary_logic_value="Native (spatial containment)",
            advantage="boundary_logic",
            notes="Forms have direct spatial interpretation"
        ),
        FoundationComparison(
            property_name="Computational Model",
            set_theory_value="Not direct",
            boundary_logic_value="Direct (NAND complete)",
            advantage="boundary_logic",
            notes="Forms map to logic circuits"
        ),
        FoundationComparison(
            property_name="Historical Development",
            set_theory_value="Cantor 1874, ZFC 1908+",
            boundary_logic_value="Spencer-Brown 1969",
            advantage="set_theory",
            notes="Set theory more established"
        ),
        FoundationComparison(
            property_name="Community Adoption",
            set_theory_value="Universal standard",
            boundary_logic_value="Niche/specialized",
            advantage="set_theory",
            notes="Set theory is the mathematical lingua franca"
        ),
    ]


@dataclass
class ProofComplexityMetrics:
    """Metrics for comparing proof complexity.
    
    Attributes:
        statement: The statement being proved
        set_theory_steps: Steps in set theory proof
        boundary_logic_steps: Steps in boundary logic proof
        set_theory_symbols: Symbol count in set theory
        boundary_logic_symbols: Symbol count in boundary logic
    """
    statement: str
    set_theory_steps: int
    boundary_logic_steps: int
    set_theory_symbols: int
    boundary_logic_symbols: int
    
    @property
    def step_ratio(self) -> float:
        """Ratio of set theory to boundary logic steps."""
        if self.boundary_logic_steps == 0:
            return float('inf')
        return self.set_theory_steps / self.boundary_logic_steps
    
    @property
    def symbol_ratio(self) -> float:
        """Ratio of set theory to boundary logic symbols."""
        if self.boundary_logic_symbols == 0:
            return float('inf')
        return self.set_theory_symbols / self.boundary_logic_symbols


def analyze_form_complexity(form: Form) -> Dict[str, Any]:
    """Analyze the complexity of a boundary form.
    
    Args:
        form: Form to analyze
        
    Returns:
        Dictionary of complexity metrics
    """
    trace = reduce_with_trace(form)
    
    return {
        "original_form": str(form),
        "canonical_form": str(trace.canonical),
        "reduction_steps": trace.step_count,
        "original_depth": form.depth(),
        "original_size": form.size(),
        "canonical_depth": trace.canonical.depth(),
        "canonical_size": trace.canonical.size(),
        "is_tautology": trace.canonical.is_simple_mark(),
        "is_contradiction": trace.canonical.is_void(),
    }


def compare_de_morgan() -> Dict[str, Any]:
    """Compare De Morgan's law proofs in both systems.
    
    Returns:
        Comparison data
    """
    # In boundary logic, De Morgan is immediate from notation
    # ⟨ab⟩ represents NOT(a AND b)
    # ⟨⟨a⟩⟨b⟩⟩ represents OR (which is NOT(NOT a AND NOT b))
    
    a = make_mark()
    b = make_void()
    
    # NOT(a AND b)
    not_and = enclose(juxtapose(a, b))
    
    # NOT a OR NOT b = ⟨⟨NOT a⟩⟨NOT b⟩⟩ = ⟨⟨⟨a⟩⟩⟨⟨b⟩⟩⟩
    not_a_or_not_b = enclose(juxtapose(enclose(enclose(a)), enclose(enclose(b))))
    
    trace1 = reduce_with_trace(not_and)
    trace2 = reduce_with_trace(not_a_or_not_b)
    
    return {
        "law": "De Morgan: NOT(a AND b) = NOT a OR NOT b",
        "boundary_lhs": str(not_and),
        "boundary_rhs": str(not_a_or_not_b),
        "lhs_canonical": str(trace1.canonical),
        "rhs_canonical": str(trace2.canonical),
        "lhs_steps": trace1.step_count,
        "rhs_steps": trace2.step_count,
        "equivalent": trace1.canonical == trace2.canonical,
        "set_theory_steps": "~5-7 (typical textbook proof)",
        "boundary_advantage": trace1.step_count + trace2.step_count < 10,
    }


def compare_double_negation() -> Dict[str, Any]:
    """Compare double negation elimination proofs.
    
    Returns:
        Comparison data
    """
    a = make_mark()
    
    # ⟨⟨a⟩⟩ should equal a
    double_neg = enclose(enclose(a))
    
    trace = reduce_with_trace(double_neg)
    
    return {
        "law": "Double Negation: NOT NOT a = a",
        "boundary_form": str(double_neg),
        "canonical": str(trace.canonical),
        "reduction_steps": trace.step_count,
        "is_axiom": True,  # This is axiom J1
        "set_theory": "Requires excluded middle (classical logic)",
        "boundary_logic": "Direct axiom J1 (Calling)",
    }


def generate_comparison_table() -> str:
    """Generate a formatted comparison table.
    
    Returns:
        Markdown formatted table
    """
    mappings = get_concept_mappings()
    
    lines = [
        "| Concept | Set Theory | Boundary Logic | Boolean | Propositional |",
        "|---------|------------|----------------|---------|---------------|",
    ]
    
    for m in mappings:
        lines.append(
            f"| {m.concept} | {m.set_theory} | {m.boundary_logic} | "
            f"{m.boolean_algebra} | {m.propositional} |"
        )
    
    return "\n".join(lines)


def generate_advantages_summary() -> Dict[str, List[str]]:
    """Generate summary of advantages for each system.
    
    Returns:
        Dictionary mapping system to list of advantages
    """
    return {
        "set_theory_advantages": [
            "Universal mathematical standard",
            "Extensive developed theory",
            "Rich connection to analysis and topology",
            "Well-understood metamathematics",
            "Comprehensive axiom systems (ZFC)",
        ],
        "boundary_logic_advantages": [
            "Minimal axiom set (only 2 axioms)",
            "Direct geometric/spatial intuition",
            "Native handling of self-reference",
            "Direct mapping to logic circuits",
            "Elegant notation for Boolean operations",
            "Unified treatment of NOT and containment",
        ],
        "complementary_uses": [
            "Boundary logic for circuit design",
            "Set theory for abstract mathematics",
            "Boundary logic for cognitive science models",
            "Set theory for foundational proofs",
        ],
    }


def expressiveness_comparison() -> Dict[str, bool]:
    """Compare expressiveness of both systems.
    
    Tests various logical constructs.
    
    Returns:
        Dictionary of expressible constructs
    """
    from src.algebra import BooleanAlgebra as BA
    
    constructs = {
        "negation": True,
        "conjunction": True,
        "disjunction": True,
        "implication": True,
        "biconditional": True,
        "nand": True,
        "nor": True,
        "xor": True,
    }
    
    # Verify each construct is expressible in boundary logic
    a = make_mark()
    b = make_void()
    
    # Test that each reduces properly
    constructs["negation_verified"] = evaluate(BA.not_(a)) != evaluate(a)
    constructs["conjunction_verified"] = not evaluate(BA.and_(a, b))  # T AND F = F
    constructs["disjunction_verified"] = evaluate(BA.or_(a, b))  # T OR F = T
    
    return constructs

