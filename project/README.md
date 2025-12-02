# Containment Theory: Boundary Logic as Alternative Foundation

This project provides a comprehensive computational framework for **Containment Theory**—an alternative foundation to classical Set Theory based on G. Spencer-Brown's *Laws of Form* (1969). The calculus of indications uses spatial containment (boundaries) rather than set membership as its primitive notion.

## Core Concepts

### The Primary Distinction

The fundamental operation is **making a distinction**—creating a boundary that separates inside from outside. This is represented by the **mark**:

```
⟨ ⟩  (mark = TRUE)
```

The absence of a mark is the **void**:

```
    (void = FALSE)
```

### Two Axioms

The entire Boolean algebra derives from just two axioms:

1. **Calling (J1)**: `⟨⟨a⟩⟩ = a` — Double enclosure returns to original
2. **Crossing (J2)**: `⟨ ⟩⟨ ⟩ = ⟨ ⟩` — Multiple marks condense to one

### Boolean Correspondence

| Operation | Boolean | Boundary Form |
|-----------|---------|---------------|
| TRUE | 1 | `⟨ ⟩` |
| FALSE | 0 | void |
| NOT a | ¬a | `⟨a⟩` |
| a AND b | a ∧ b | `ab` |
| a OR b | a ∨ b | `⟨⟨a⟩⟨b⟩⟩` |
| a NAND b | ¬(a ∧ b) | `⟨ab⟩` |

## Project Structure

```
project/
├── src/                    # Core implementation
│   ├── forms.py            # Form class and construction
│   ├── reduction.py        # Reduction engine
│   ├── algebra.py          # Boolean algebra correspondence
│   ├── evaluation.py       # Truth value extraction
│   ├── theorems.py         # Theorem definitions
│   ├── verification.py     # Formal verification
│   ├── complexity.py       # Complexity analysis
│   ├── comparison.py       # Set Theory comparison
│   ├── visualization.py    # Form visualization
│   └── diagrams.py         # Publication figures
├── tests/                  # Comprehensive test suite
├── scripts/                # Analysis workflows
├── manuscript/             # Research manuscript
└── output/                 # Generated artifacts
```

## Quick Start

```python
from src.forms import make_void, make_mark, enclose, juxtapose
from src.reduction import reduce_form

# Create forms
void = make_void()      # FALSE
mark = make_mark()      # TRUE

# Boolean operations
not_a = enclose(mark)   # NOT TRUE = FALSE
a_and_b = juxtapose(mark, mark)  # TRUE AND TRUE

# Reduce to canonical form
result = reduce_form(a_and_b)
print(result)  # ⟨⟩ (mark = TRUE)
```

## Key Features

- **Complete Boolean Algebra**: All operations derived from two axioms
- **Polynomial-Time Reduction**: Efficient canonical form computation
- **Formal Verification**: Computational proof of all theorems
- **Visualization**: Nested boundary diagrams
- **70%+ Test Coverage**: Rigorous verification with real data

## Running Tests

```bash
# Run all project tests
python3 -m pytest project/tests/ -v

# With coverage
python3 -m pytest project/tests/ --cov=project/src --cov-report=html
```

## Generating Manuscript

```bash
# Full pipeline
python3 scripts/run_all.py

# Or use the interactive menu
./run.sh
```

## Philosophical Foundations

This implementation is grounded in:
- **North American Pragmatism** (Peirce, James, Dewey)
- **Process Philosophy** (Whitehead)
- **Neo-Materialism** (Barad, Haraway, Bennett)

See `manuscript/S03_supplemental_analysis.md` for comprehensive philosophical context.

## References

- Spencer-Brown, G. (1969). *Laws of Form*. Allen & Unwin.
- Kauffman, L. H. (2001). The Mathematics of Charles Sanders Peirce. *Cybernetics & Human Knowing*.
- Bricken, W. (2019). *Iconic Arithmetic Volume I*. Unary Press.

## License

Apache 2.0 — See LICENSE file for details.
