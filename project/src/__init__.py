"""Containment Theory: Boundary Logic as Alternative Foundation to Set Theory.

This package implements the computational framework for G. Spencer-Brown's
Laws of Form (1969), providing tools for:

- Form construction and manipulation
- Reduction to canonical forms
- Boolean algebra isomorphism
- Theorem verification
- Visualization and publication figures

Core Concepts:
    - Form: A recursive structure of nested boundaries
    - Mark: The primary distinction ⟨ ⟩ (TRUE)
    - Void: Empty space (FALSE)
    - Enclosure: ⟨a⟩ represents NOT a
    - Juxtaposition: ab represents a AND b

Axioms:
    1. Calling (J1): ⟨⟨a⟩⟩ = a (double crossing returns)
    2. Crossing (J2): ⟨ ⟩⟨ ⟩ = ⟨ ⟩ (marks condense)

Example:
    >>> from src.forms import Form, make_mark, make_void, enclose
    >>> from src.reduction import reduce_form
    >>> 
    >>> # Create ⟨⟨⟨ ⟩⟩⟩ (triple enclosed mark)
    >>> form = enclose(enclose(make_mark()))
    >>> print(form)  # ⟨⟨⟨ ⟩⟩⟩
    >>> 
    >>> # Reduce to canonical form
    >>> canonical = reduce_form(form)
    >>> print(canonical)  # ⟨ ⟩ (by calling axiom)
"""
from src.forms import (
    Form,
    FormType,
    make_void,
    make_mark,
    make_cross,
    enclose,
    juxtapose,
    negate,
    conjunction,
    disjunction,
    implication,
    equivalence,
    forms_equal,
    is_canonical,
)

from src.reduction import (
    ReductionEngine,
    ReductionStep,
    ReductionTrace,
    ReductionRule,
    reduce_form,
    reduce_with_trace,
    forms_equivalent,
    canonical_form,
    demonstrate_calling,
    demonstrate_crossing,
)

from src.algebra import (
    BooleanValue,
    BooleanExpression,
    BooleanAlgebra,
    boolean_to_form,
    form_to_boolean,
    evaluate_form,
    verify_de_morgan_laws,
    verify_boolean_axioms,
    is_tautology,
    is_contradiction,
    is_satisfiable,
)

from src.expressions import (
    ExpressionParser,
    ExpressionGenerator,
    parse_expression,
    parse,
    generate_random_form,
    generate_test_suite,
    format_form,
)

from src.evaluation import (
    EvaluationResult,
    EvaluationContext,
    FormEvaluator,
    evaluate,
    evaluate_with_trace,
    truth_value,
    is_true,
    is_false,
    analyze_form,
    SemanticAnalysis,
)

from src.theorems import (
    Theorem,
    TheoremStatus,
    Proof,
    ProofStep,
    axiom_calling,
    axiom_crossing,
    theorem_position,
    theorem_generation,
    theorem_iteration,
    get_all_axioms,
    get_all_consequences,
    get_all_theorems,
    verify_all_theorems,
    theorem_summary,
)

from src.comparison import (
    NotationSystem,
    ConceptMapping,
    FoundationComparison,
    get_concept_mappings,
    get_foundation_comparisons,
    analyze_form_complexity,
    compare_de_morgan,
    generate_comparison_table,
    generate_advantages_summary,
)

from src.complexity import (
    ComplexityMetrics,
    ComplexityAnalysis,
    ComplexityAnalyzer,
    analyze_reduction_complexity,
    complexity_scaling_analysis,
    termination_analysis,
    compare_to_sat,
    generate_complexity_report,
)

from src.verification import (
    VerificationStatus,
    VerificationResult,
    VerificationReport,
    AxiomVerifier,
    ConsistencyVerifier,
    EquivalenceVerifier,
    SemanticVerifier,
    verify_axioms,
    verify_consistency,
    verify_semantics,
    full_verification,
    generate_verification_summary,
)

from src.visualization import (
    VisualizationStyle,
    FormVisualizer,
    ReductionVisualizer,
    visualize_form,
    save_form_figure,
    visualize_reduction,
    create_axiom_diagram,
    create_boolean_correspondence_diagram,
    VisualizationEngine,
    create_multi_panel_figure,
)

from src.diagrams import (
    DiagramStyle,
    PublicationDiagramGenerator,
    generate_all_figures,
)

__version__ = "1.0.0"
__author__ = "Project Author"
__description__ = "Containment Theory: Boundary Logic Implementation"

__all__ = [
    # Forms
    "Form",
    "FormType",
    "make_void",
    "make_mark",
    "make_cross",
    "enclose",
    "juxtapose",
    "negate",
    "conjunction",
    "disjunction",
    "implication",
    "equivalence",
    "forms_equal",
    "is_canonical",
    
    # Reduction
    "ReductionEngine",
    "ReductionStep",
    "ReductionTrace",
    "ReductionRule",
    "reduce_form",
    "reduce_with_trace",
    "forms_equivalent",
    "canonical_form",
    
    # Algebra
    "BooleanValue",
    "BooleanExpression",
    "BooleanAlgebra",
    "boolean_to_form",
    "form_to_boolean",
    "is_tautology",
    "is_contradiction",
    "is_satisfiable",
    
    # Expressions
    "parse_expression",
    "parse",
    "generate_random_form",
    "format_form",
    
    # Evaluation
    "evaluate",
    "evaluate_with_trace",
    "truth_value",
    "is_true",
    "is_false",
    "analyze_form",
    
    # Theorems
    "Theorem",
    "axiom_calling",
    "axiom_crossing",
    "get_all_theorems",
    "verify_all_theorems",
    "theorem_summary",
    
    # Verification
    "verify_axioms",
    "verify_consistency",
    "verify_semantics",
    "full_verification",
    
    # Visualization
    "visualize_form",
    "visualize_reduction",
    "create_axiom_diagram",
    "generate_all_figures",
    "VisualizationEngine",
    "create_multi_panel_figure",
]
