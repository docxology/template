# AI Agent Instructions — template_code_project Exemplar

## Why This File Exists

`template_code_project` is the **control positive** for the template repository: the canonical example proving that the computational-research path works correctly. Deviating from the rules below — introducing a mock, moving math to scripts/, breaking the src/infrastructure boundary — breaks the exemplar purpose and misleads future users who study this project to understand how the template works.

Read this file before touching any other file in this project.

---

## Rule 1: Read the Hub First

Reading order is mandatory, not advisory. Each document gates a category of action:

| Document | Governs | Skip consequence |
|---|---|---|
| **This file** | All modifications | Risk all violations below |
| [`architecture.md`](architecture.md) | Any file-boundary change | Risk violating src/scripts boundary |
| [`testing_philosophy.md`](testing_philosophy.md) | Any test modification | Risk introducing mocks or reducing coverage |
| [`rendering_pipeline.md`](rendering_pipeline.md) | Any manuscript or output change | Risk unresolved `{{VARIABLE}}` tokens in PDF |
| [`style_guide.md`](style_guide.md) | Any source code modification | Risk mock usage, wrong import layer, bad error messages |
| [`syntax_guide.md`](syntax_guide.md) | Any manuscript `.md` modification | Risk hardcoded numbers, broken figure references |

---

## Rule 2: Coverage Gate — ≥90% on `src/`

The test suite spans `test_optimizer.py` (pure math), `test_analysis_integration.py` (orchestration), `test_analysis_coverage.py` (orchestration branches and error paths), `test_experiment_config.py`, `test_figures_orchestration.py`, `test_dashboard_config.py`, `test_invariants.py`, `test_invariants_and_dashboard.py`, `test_manuscript_variables.py`, and `test_scripts_smoke.py` (auxiliary script smoke). Both the project `pyproject.toml` and the root pipeline gate coverage at **90%**. Live test count + current coverage percentage live in [`docs/_generated/canonical_facts.md`](../../../docs/_generated/canonical_facts.md) — do not hardcode either number in prose, because both drift faster than the docs touching them.

Before modifying `src/optimizer.py`, count the existing tests for the function you are changing. After modifying, run:

```bash
uv run pytest projects/template_code_project/tests/ \
    --cov=projects/template_code_project/src \
    --cov-fail-under=90 \
    --cov-report=term-missing \
    -v
```

If coverage drops, do not delete tests to make the number work — fix the gap.

---

## Rule 3: The Thin Orchestrator Boundary — `scripts/` vs `src/`

**`src/optimizer.py`** contains pure mathematical functions: no file I/O, no infrastructure imports, no side-effects, stdlib `logging` only.

**`scripts/*.py`** contains experiment coordination: loops over step sizes, calls to `src/` functions, delegation to `infrastructure.*`, writing CSVs and PNGs.

**The boundary test**: If a line of code in `scripts/` contains a mathematical expression that determines the algorithm's output (a gradient, an update step, a convergence check), it violates the boundary. Move that expression to `src/` and write a test for it.

**Forbidden**:
```python
# In scripts/optimization_analysis.py — BAD
x = x - alpha * (x - 1.0)   # Gradient update rule belongs in src/
```

**Correct**:
```python
# In scripts/optimization_analysis.py — GOOD
result = gradient_descent(x0, obj_func, grad_func, step_size=alpha)
```

---

## Rule 4: "Show, Not Tell" Documentation

When updating `manuscript/` files, use explicit, verifiable references instead of vague descriptions.

**BAD** (vague, unverifiable):
```markdown
Our testing framework validates numerical accuracy using standard approaches.
```

**GOOD** (concrete, linkable):
```markdown
`projects/template_code_project/tests/test_optimizer.py::TestComputeGradient` validates gradient
accuracy against analytical solutions without mocks, using `numpy` arrays with known values.
```

**BAD** (vague):
```markdown
The infrastructure renders the manuscript to PDF automatically.
```

**GOOD** (concrete):
```markdown
`infrastructure/rendering/pdf_renderer.py` orchestrates Pandoc → pdflatex to produce
`output/template_code_project/pdf/template_code_project_combined.pdf` from the substituted markdown in `output/manuscript/`.
```

---

## Rule 5: Determinism Policy

Prefer fixed inputs in `src/` and tests. When a test uses random draws (e.g., timing on large random arrays), two requirements apply:

1. Assertions must use **bounds** (`assert elapsed < 5.0`), not exact values (`assert elapsed == 0.003`).
2. The test docstring must explain why timing is the relevant property to check.

Fixed seeds are acceptable for `numpy.random` in timing tests:
```python
rng = np.random.default_rng(42)
large_A = rng.standard_normal((50, 50))
```

Prefer analytical inputs over random inputs whenever a mathematical property can be directly verified.

---

## Rule 6: Style and Syntax Guides Govern Their Domains

- **[`style_guide.md`](style_guide.md)** governs: `src/optimizer.py`, `tests/test_optimizer.py`, `scripts/*.py` — mock prohibition, infrastructure delegation, thin orchestrator, error message format, type hints.
- **[`syntax_guide.md`](syntax_guide.md)** governs: `manuscript/*.md` — `{{VARIABLE}}` injection, `[@label]` Pandoc-crossref cross-references, figure labels, table captions.

Do not apply code-style rules to manuscript prose, and do not apply manuscript syntax rules to Python source.

---

## Rule 7: `output/` Is Disposable — Never Edit Generated Files

The entire `projects/template_code_project/output/` tree is written by the pipeline and overwritten on every run. Editing a file in `output/` has zero lasting effect and will confuse future agents.

If you need to change what a generated file contains, change the **generator**:
- To change `output/data/optimization_results.csv` → modify `scripts/optimization_analysis.py`
- To change `output/manuscript/03_results.md` → modify `manuscript/03_results.md` (the template) and/or `scripts/z_generate_manuscript_variables.py` (the variable definitions)
- To change `output/pdf/template_code_project_combined.pdf` → modify the manuscript source files, then re-render

See [`output_conventions.md`](output_conventions.md) for the complete regeneration sequence.

---

## Verification Checklist

Run all three commands before submitting any change to this project:

```bash
# 1. Tests pass and coverage gate is met
uv run pytest projects/template_code_project/tests/ \
    --cov=projects/template_code_project/src \
    --cov-fail-under=90 -q

# 2. No mocks exist anywhere in tests/
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" \
    projects/template_code_project/tests/ || echo "Clean — no mocks found"

# 3. The mathematical primitives (optimizer.py, invariants.py) have no infrastructure imports.
#    These two files MUST remain infrastructure-free so they are copy-pasteable into any
#    Python environment without the pipeline installed. Other `src/` modules (`analysis.py`,
#    `dashboard.py`, `manuscript_variables.py`) are orchestration layers and may import
#    `infrastructure.*` behind try/except fallbacks; that is intentional and documented in
#    `src/AGENTS.md` and `architecture.md`.
grep -nE "^(from|import) infrastructure" \
    projects/template_code_project/src/optimizer.py \
    projects/template_code_project/src/invariants.py \
    && echo "VIOLATION — math primitive imports infrastructure" \
    || echo "Clean — math primitives are infrastructure-free"
```

All three must produce zero violations (or the "Clean" message for checks 2 and 3).
