# Frequently Asked Questions

## Architecture and workflow

### Why can't `src/eda/` import from `infrastructure/`?

`src/eda/` is pure data logic. It must run in any Python environment with only
numpy and pandas installed. All cross-cutting concerns (rendering, validation,
logging) are delegated to `infrastructure/` and called from `scripts/`. This
keeps the library testable with zero mocks and reusable outside the pipeline.

### What is the "thin orchestrator" pattern?

The notebook and `scripts/eda_analysis.py` should not implement analysis logic.
They should:

- Import functions from `src/eda/`.
- Plot the returned data with matplotlib.
- Write outputs to `output/`.

If you find yourself computing a statistic or correlation inside a cell or
script, move it to `src/eda/` and add a test.

### Why are mocks forbidden?

Mocking tests that a function *was called*, not that it produced the *correct
result*. Pure data transforms can be tested with the real shipped CSV or a tiny
real frame and expected outputs. Mocks give a false sense of correctness and
break the reproducibility guarantee.

## Testing and coverage

### Why 90% coverage? Can I lower it?

The gate ensures `src/eda/` logic is thoroughly exercised. If coverage drops, it
signals a missing test — add it, don't lower the gate.

### My new function lowered coverage. What now?

Write tests for the new function in the matching `tests/test_*.py`. Use the
shipped CSV or a hand-built frame with values chosen so the expected result is
exact.

### Do I need to test the script and notebook?

Yes. `tests/test_eda_analysis_script.py` runs `run_eda()` against a temp output
root and asserts real artifacts are written. `tests/test_notebook.py` checks the
notebook is valid nbformat, binds to `src.__all__`, and carries no logic in
cells.

## Manuscript and rendering

### How do I add a new figure?

1. Add a figure-data preparer to `src/eda/figures.py` (returns a dataclass of
   numbers; no matplotlib) with a test in `tests/test_figures.py`.
2. Plot it in `scripts/eda_analysis.py` and write the PNG to `output/figures/`.
3. In `manuscript/03_results.md`, add a Pandoc image line:
   ```markdown
   ![Caption text.](../output/figures/my_figure.png){#fig:my_label}
   ```
4. Reference it in prose: `See [@fig:my_label].`
5. Update [`syntax_guide.md`](syntax_guide.md) with the new figure label.

### Does this exemplar use `{{VARIABLE}}` token injection?

No. Concrete numbers are reproduced by running `scripts/eda_analysis.py`, and
numeric claims in prose are registered in `data/claim_ledger.yaml`. The
manuscript describes structure and provenance rather than transcribing volatile
values.

## Common pitfalls

### I imported `infrastructure` in `src/eda/` and tests broke

`src/eda/` must stay infrastructure-free. Move that code to `scripts/`.

### My test uses `unittest.mock` and the drift gate failed

Replace the mock with real data. Mocks are forbidden — call the actual function
with the shipped CSV or a real frame and assert the result.

### The analysis script runs but `output/figures/` is empty

Check the exit code and look for errors. Ensure you ran the script with `uv run`
from the repository root so imports resolve.

## See also

- [`quickstart.md`](quickstart.md) — basic commands.
- [`troubleshooting.md`](troubleshooting.md) — symptom-driven recipes.
- [`output_conventions.md`](output_conventions.md) — output regeneration rules.
- [`syntax_guide.md`](syntax_guide.md) — Pandoc-crossref syntax.
- [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) — figure protocol.
