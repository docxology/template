# AI Agent Instructions — template_eda_notebook Exemplar

## Why This File Exists

`template_eda_notebook` is the **control positive** for the EDA / computational
notebook path: the canonical example proving an exploratory analysis can stay
reproducible by delegating every computation to a tested library. Deviating from
the rules below — introducing a mock, putting analysis logic in a notebook cell
or script, breaking the `src/`/`infrastructure` boundary — breaks the exemplar's
purpose.

Read this file before touching any other file in this project.

---

## Rule 1: Read the Hub First

| Document | Governs | Skip consequence |
|---|---|---|
| **This file** | All modifications | Risk all violations below |
| [`architecture.md`](architecture.md) | Any file-boundary change | Risk violating the src/scripts boundary |
| [`testing_philosophy.md`](testing_philosophy.md) | Any test modification | Risk introducing mocks or reducing coverage |
| [`rendering_pipeline.md`](rendering_pipeline.md) | Any manuscript or output change | Risk broken figure references in the PDF |
| [`style_guide.md`](style_guide.md) | Any source code modification | Risk impure library code, wrong import layer |
| [`syntax_guide.md`](syntax_guide.md) | Any manuscript `.md` modification | Risk broken figure references |

---

## Rule 2: Coverage Gate — ≥90% on `src/`

The suite spans `test_dataset.py`, `test_cleaning.py`, `test_statistics.py`,
`test_correlation.py`, `test_figures.py`, `test_project_paths.py`,
`test_eda_analysis_script.py`, and `test_notebook.py`. Both the project
`pyproject.toml` and the root pipeline gate coverage at **90%**. Live test count
and coverage live in [`docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md) —
do not hardcode either number in prose.

After modifying any `src/eda/` module, run:

```bash
uv run pytest projects/templates/template_eda_notebook/tests \
    --cov=projects/templates/template_eda_notebook/src \
    --cov-fail-under=90 --cov-report=term-missing -v
```

If coverage drops, fix the gap — do not delete tests to make the number work.

---

## Rule 3: The Thin Orchestrator Boundary

**`src/eda/*.py`** contains pure data transforms: no plotting, no file I/O, no
`infrastructure.*` imports.

**`scripts/eda_analysis.py`** and **notebook cells** coordinate: they call `src`
functions, plot the returned data, and write files.

**The boundary test**: if a notebook cell or script computes a statistic,
correlation, or any analysis result inline, it violates the boundary. Move that
computation into `src/eda/` and write a test.

```python
# In a cell or script — BAD
corr = frame["height_cm"].corr(frame["weight_kg"])  # analysis logic

# GOOD
matrix = correlation_matrix(frame)  # tested src function
```

---

## Rule 4: "Show, Not Tell" Documentation

Use explicit, verifiable references in `manuscript/` files.

**GOOD**: `src/eda/correlation.py::strongest_pairs()` ranks feature pairs by
absolute correlation while preserving sign.

**BAD**: "The library finds the most related features."

---

## Rule 5: Determinism Policy

The shipped CSV is generated once with a fixed seed; the figure-data preparers
have no RNG. Prefer fixed, hand-chosen inputs in tests so the expected statistic
is exact. If you ever introduce randomness, seed it and assert bounds, not exact
values.

---

## Rule 6: Style and Syntax Guides Govern Their Domains

- **[`style_guide.md`](style_guide.md)** governs `src/eda/*.py`, `tests/`, and
  `scripts/`.
- **[`syntax_guide.md`](syntax_guide.md)** governs `manuscript/*.md`.

Do not apply code-style rules to manuscript prose or vice versa.

---

## Rule 7: `output/` Is Disposable — Never Edit Generated Files

The entire `output/` tree is written by the pipeline and overwritten on every
run. To change what a generated file contains, change the **generator**:

- To change `output/figures/*.png` or `output/data/summary_statistics.csv` →
  modify `src/eda/` and/or `scripts/eda_analysis.py`, then re-run the script.
- To change the rendered PDF → modify the `manuscript/*.md` source, then
  re-render.

See [`output_conventions.md`](output_conventions.md).

---

## Verification Checklist

```bash
# 1. Tests pass and coverage gate is met
uv run pytest projects/templates/template_eda_notebook/tests \
    --cov=projects/templates/template_eda_notebook/src --cov-fail-under=90 -q

# 2. No mocks anywhere in tests/
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" \
    projects/templates/template_eda_notebook/tests/ || echo "Clean — no mocks found"

# 3. The EDA library has no infrastructure imports
grep -rnE "^(from|import) infrastructure" \
    projects/templates/template_eda_notebook/src/ \
    && echo "VIOLATION — src/ imports infrastructure" \
    || echo "Clean — the EDA library is infrastructure-free"
```
