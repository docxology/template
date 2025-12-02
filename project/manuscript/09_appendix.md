# Appendix

## A. Complete Axiom Derivations

### A.1 Calling Axiom (J1) Proof

**Statement**: $\langle\langle a \rangle\rangle = a$

**Spatial Interpretation**:
Consider a space with form $a$. Enclosing $a$ creates $\langle a \rangle$—we are now "outside" $a$ (inside the boundary around $a$). Enclosing again creates $\langle\langle a \rangle\rangle$—we are now "outside" of being "outside" $a$, which returns us to $a$.

**Algebraic Proof**:
Let $\llbracket \cdot \rrbracket$ denote truth value evaluation.
- $\llbracket\langle\langle a \rangle\rangle\rrbracket = \neg\llbracket\langle a \rangle\rrbracket$ (by enclosure semantics)
- $= \neg\neg\llbracket a \rrbracket$ (by enclosure semantics again)
- $= \llbracket a \rrbracket$ (by double negation)

Since truth values are preserved and the calculus is sound, $\langle\langle a \rangle\rangle = a$.

### A.2 Crossing Axiom (J2) Proof

**Statement**: $\langle\ \rangle\langle\ \rangle = \langle\ \rangle$

**Spatial Interpretation**:
Two marks side by side both indicate "the marked state." Indicating the same state twice does not change what is indicated.

**Algebraic Proof**:
- $\llbracket\langle\ \rangle\langle\ \rangle\rrbracket = \llbracket\langle\ \rangle\rrbracket \land \llbracket\langle\ \rangle\rrbracket$ (by juxtaposition semantics)
- $= \text{TRUE} \land \text{TRUE}$ (mark is TRUE)
- $= \text{TRUE}$
- $= \llbracket\langle\ \rangle\rrbracket$

## B. Consequence Derivations

### B.1 C1: Position

**Statement**: $\langle\langle a \rangle b \rangle a = a$

**Derivation**:
Consider the Boolean interpretation:
- LHS = $\neg(\neg a \land b) \land a$
- $= (a \lor \neg b) \land a$ (De Morgan)
- $= a \land (a \lor \neg b)$ (commutative)
- $= a$ (absorption)

### B.2 C3: Generation (Law of Excluded Middle)

**Statement**: $\langle\langle a \rangle a \rangle = \langle\ \rangle$

**Derivation**:
- LHS = $\langle\langle a \rangle a \rangle$
- $= \neg(\neg a \land a)$ (Boolean interpretation)
- $= \neg(\text{FALSE})$ (contradiction)
- $= \text{TRUE}$
- $= \langle\ \rangle$

This confirms that $a \lor \neg a = \text{TRUE}$.

### B.3 C6: Iteration (Idempotence)

**Statement**: $aa = a$

**Derivation**:
- $\llbracket aa \rrbracket = \llbracket a \rrbracket \land \llbracket a \rrbracket$ (juxtaposition)
- $= \llbracket a \rrbracket$ (idempotence of AND)

## C. Boolean Algebra Correspondence

### C.1 Complete Translation Table

| Boolean | Boundary Form | Reduction |
|---------|---------------|-----------|
| TRUE | $\langle\ \rangle$ | canonical |
| FALSE | void | canonical |
| $\neg a$ | $\langle a \rangle$ | — |
| $a \land b$ | $ab$ | — |
| $a \lor b$ | $\langle\langle a \rangle\langle b \rangle\rangle$ | — |
| $a \to b$ | $\langle a\langle b \rangle\rangle$ | — |
| $a \leftrightarrow b$ | $\langle\langle ab \rangle\langle\langle a \rangle\langle b \rangle\rangle\rangle$ | — |
| $a \oplus b$ (XOR) | $\langle\langle\langle a \rangle b \rangle\langle a\langle b \rangle\rangle\rangle$ | — |
| $a$ NAND $b$ | $\langle ab \rangle$ | — |
| $a$ NOR $b$ | $\langle\langle\langle a \rangle\langle b \rangle\rangle\rangle$ | — |

### C.2 NAND Completeness

All Boolean operations expressible via NAND ($\langle ab \rangle$):

- NOT $a$ = $a$ NAND $a$ = $\langle aa \rangle = \langle a \rangle$
- $a$ AND $b$ = NOT($a$ NAND $b$) = $\langle\langle ab \rangle\rangle = ab$
- $a$ OR $b$ = (NOT $a$) NAND (NOT $b$) = $\langle\langle a \rangle\langle b \rangle\rangle$

## D. Reduction Algorithm Details

### D.1 Pattern Matching

**Calling Pattern**:
```
Match: Form with is_marked=True, contents=[Form with is_marked=True, contents=[a]]
Result: a
```

**Crossing Pattern**:
```
Match: Form with multiple simple marks in contents
Result: Single mark with non-mark contents preserved
```

### D.2 Trace Format

Each reduction step records:
```
ReductionStep:
  - before: Form (pre-reduction)
  - after: Form (post-reduction)
  - rule: ReductionRule (CALLING | CROSSING | VOID_ELIMINATION)
  - location: str (where rule applied)
```

### D.3 Termination Proof

**Theorem**: The reduction algorithm terminates for all well-formed inputs.

**Proof**:
Define measure $\mu(f) = (\text{depth}(f), \text{size}(f))$ with lexicographic ordering.

1. **Calling**: Reduces depth by 2 (removes two enclosures)
2. **Crossing**: Reduces size (removes marks)
3. **Void Elimination**: Reduces size (removes void)
4. **Recursive**: Applies to subforms with strictly smaller measure

Each rule application strictly decreases $\mu(f)$. Since $\mu(f) \geq (0, 0)$ and the ordering is well-founded, the algorithm terminates. $\square$

## E. Test Coverage Details

### E.1 Test Categories

| Category | Tests | Coverage Target |
|----------|-------|-----------------|
| Unit (forms.py) | 36 | 95%+ |
| Unit (reduction.py) | 27 | 95%+ |
| Unit (algebra.py) | 22 | 90%+ |
| Integration | 15 | 90%+ |
| Theorem verification | 12 | 100% |
| Edge cases | 18 | Comprehensive |

### E.2 Property-Based Testing

Random form generation tests:
- Depth: 1-6 (uniform)
- Width: 1-4 (uniform)
- Samples: 500 per test run
- Seed: 42 (reproducible)

Verified properties:
- All forms reduce to canonical
- Canonical forms are stable (re-reduction yields same)
- Equivalent forms have equal canonical forms

## F. Notation Reference

| Symbol | Meaning | LaTeX |
|--------|---------|-------|
| $\langle\ \rangle$ | Mark (TRUE) | `\langle\ \rangle` |
| $\emptyset$ | Void (FALSE) | `\emptyset` |
| $\langle a \rangle$ | Enclosure (NOT) | `\langle a \rangle` |
| $ab$ | Juxtaposition (AND) | `ab` |
| $\llbracket f \rrbracket$ | Truth value | `\llbracket f \rrbracket` |
| $j$ | Imaginary value | `j` |

## G. Implementation Reference

### G.1 Module Structure

```
project/src/
├── forms.py        # Form class and construction
├── reduction.py    # Reduction engine
├── algebra.py      # Boolean correspondence
├── evaluation.py   # Truth value extraction
├── theorems.py     # Theorem definitions
├── verification.py # Formal verification
├── visualization.py # Diagram generation
└── __init__.py     # Package exports
```

### G.2 Key APIs

```python
# Form construction
make_void() -> Form
make_mark() -> Form
enclose(form: Form) -> Form
juxtapose(*forms: Form) -> Form

# Reduction
reduce_form(form: Form) -> Form
reduce_with_trace(form: Form) -> Tuple[Form, ReductionTrace]

# Evaluation
evaluate(form: Form) -> EvaluationResult
truth_value(form: Form) -> bool

# Verification
verify_axioms() -> VerificationReport
full_verification() -> VerificationReport
```
