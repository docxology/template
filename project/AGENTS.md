# project/ - Containment Theory Implementation

## Purpose

This directory contains the complete implementation of **Containment Theory**—a computational framework for G. Spencer-Brown's calculus of indications (*Laws of Form*, 1969). The project demonstrates boundary logic as an alternative foundation to Set Theory, achieving Boolean completeness from just two axioms.

## Directory Structure

```
project/
├── src/                        # Core scientific code (Layer 2)
│   ├── forms.py                # Form class and construction primitives
│   ├── reduction.py            # Reduction engine with proof traces
│   ├── algebra.py              # Boolean algebra isomorphism
│   ├── evaluation.py           # Truth value extraction
│   ├── theorems.py             # Spencer-Brown's consequences (C1-C9)
│   ├── verification.py         # Formal verification framework
│   ├── complexity.py           # Reduction complexity analysis
│   ├── comparison.py           # Set Theory comparison metrics
│   ├── expressions.py          # Expression parsing and generation
│   ├── visualization.py        # Nested boundary diagrams
│   ├── diagrams.py             # Publication-quality figures
│   └── __init__.py             # Package exports
├── tests/                      # Comprehensive test suite
│   ├── test_forms.py           # Form construction tests
│   ├── test_reduction.py       # Reduction engine tests
│   ├── test_algebra.py         # Boolean correspondence tests
│   ├── test_evaluation.py      # Evaluation tests
│   ├── test_theorems.py        # Theorem verification tests
│   ├── test_verification.py    # Verification framework tests
│   └── test_complexity.py      # Complexity analysis tests
├── scripts/                    # Analysis orchestrators
│   ├── analysis_pipeline.py    # Main analysis workflow
│   └── example_figure.py       # Figure generation
├── manuscript/                 # Research manuscript
│   ├── 01_abstract.md          # Project overview
│   ├── 02_introduction.md      # Historical context
│   ├── 03_methodology.md       # Formal calculus and axioms
│   ├── 04_experimental_results.md  # Computational verification
│   ├── 05_discussion.md        # Set Theory comparison
│   ├── 06_conclusion.md        # Future directions
│   ├── 07_literature_review.md # Comprehensive synthesis
│   ├── S01-S04*.md             # Supplemental materials
│   └── config.yaml             # Manuscript configuration
├── output/                     # Generated artifacts
└── pyproject.toml              # Project configuration
```

## Core Modules

### forms.py - Form Construction

The fundamental data structure and operations:

```python
from src.forms import Form, make_void, make_mark, enclose, juxtapose

# Primitives
void = make_void()          # FALSE (empty space)
mark = make_mark()          # TRUE (⟨⟩)

# Operations
not_a = enclose(mark)       # ⟨⟨⟩⟩ = NOT TRUE
a_and_b = juxtapose(a, b)   # ab = a AND b

# Boolean operators
neg = negate(form)          # ⟨form⟩
conj = conjunction(a, b)    # ab
disj = disjunction(a, b)    # ⟨⟨a⟩⟨b⟩⟩
```

### reduction.py - Reduction Engine

Transforms forms to canonical representation:

```python
from src.reduction import reduce_form, reduce_with_trace, forms_equivalent

# Reduce to canonical form
canonical = reduce_form(complex_form)

# Get reduction trace (proof)
result, trace = reduce_with_trace(form)
for step in trace.steps:
    print(f"{step.rule}: {step.before} → {step.after}")

# Check equivalence
equivalent = forms_equivalent(form1, form2)
```

### algebra.py - Boolean Correspondence

Verifies isomorphism to Boolean algebra:

```python
from src.algebra import boolean_to_form, form_to_boolean, verify_de_morgan_laws

# Convert between representations
form = boolean_to_form(BooleanValue.TRUE)
value = form_to_boolean(form)

# Verify laws
result = verify_de_morgan_laws()
assert result.passed
```

### theorems.py - Spencer-Brown Consequences

All nine derived consequences:

```python
from src.theorems import axiom_calling, axiom_crossing, theorem_position

# Axioms
calling = axiom_calling(form)      # ⟨⟨a⟩⟩ = a
crossing = axiom_crossing()        # ⟨⟩⟨⟩ = ⟨⟩

# Consequences
c1 = theorem_position(a, b)        # ⟨⟨a⟩b⟩a = a
c3 = theorem_generation(a)         # ⟨⟨a⟩a⟩ = ⟨⟩ (excluded middle)
```

### verification.py - Formal Verification

Complete verification framework:

```python
from src.verification import verify_axioms, full_verification

# Verify all axioms
report = verify_axioms()
print(f"Axioms verified: {report.passed}")

# Full verification suite
full_report = full_verification()
print(full_report.summary())
```

## Two Axioms

The entire system derives from:

1. **Calling (J1)**: `⟨⟨a⟩⟩ = a`
   - Double enclosure returns to original
   - Equivalent to double negation elimination

2. **Crossing (J2)**: `⟨⟩⟨⟩ = ⟨⟩`
   - Multiple marks condense to one
   - The marked state is idempotent

## Test Coverage

The implementation maintains >70% test coverage:

| Module | Coverage |
|--------|----------|
| forms.py | 98% |
| reduction.py | 95% |
| algebra.py | 92% |
| evaluation.py | 94% |
| theorems.py | 91% |
| verification.py | 96% |

All tests use real data (no mocks) following the thin orchestrator pattern.

## Manuscript Structure

The manuscript is organized as:

1. **Abstract**: Overview of Containment Theory
2. **Introduction**: Historical context (Spencer-Brown, Kauffman, Bricken)
3. **Methodology**: Formal calculus definition
4. **Results**: Computational verification
5. **Discussion**: Comparison with Set Theory
6. **Conclusion**: Future directions
7. **Literature Review**: Comprehensive synthesis

**Supplemental Sections**:
- S01: Implementation methods
- S02: Extended results
- S03: **Pragmatist and Neo-Materialist philosophical foundations**
- S04: Applications

## Philosophical Grounding

See `manuscript/S03_supplemental_analysis.md` for comprehensive treatment of:

- **North American Pragmatism**: Peirce's existential graphs, James's radical empiricism, Dewey's inquiry
- **Process Philosophy**: Whitehead's actual entities and creativity
- **Neo-Materialism**: Barad's agential cuts, Haraway's situated knowledges
- **Continental Connections**: Deleuze's difference, Massumi's affect

## Usage

```bash
# Run tests
python3 -m pytest project/tests/ -v

# Generate manuscript
python3 scripts/run_all.py

# Interactive exploration
python3
>>> from src.forms import make_mark, enclose
>>> from src.reduction import reduce_form
>>> form = enclose(enclose(make_mark()))
>>> reduce_form(form)  # Returns mark (calling axiom)
```

## Key Insights

1. **Axiomatic Economy**: 2 axioms vs ZFC's 9+
2. **Geometric Intuition**: Boundaries as spatial operations
3. **Self-Reference**: Imaginary values instead of paradoxes
4. **Boolean Completeness**: Full propositional logic derived
5. **Polynomial Reduction**: Efficient canonical form computation

## Dependencies

- Python 3.10+
- NumPy (numerical operations)
- Matplotlib (visualization)

## See Also

- [`infrastructure/AGENTS.md`](../infrastructure/AGENTS.md) - Build system
- [`manuscript/config.yaml`](manuscript/config.yaml) - Paper configuration
- [`literature/references.bib`](../literature/references.bib) - Bibliography
