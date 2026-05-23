# Frequently Asked Questions

## Architecture and workflow

### Why can't `src/` import from `infrastructure/`?

`src/` is pure scientific logic. It must run in any Python environment
without the template's pipeline installed. All cross-cutting concerns
(logging, reporting, validation, rendering) are delegated to
`infrastructure/` and called from `scripts/`. This keeps the code
testable with zero mocks and the math reusable outside the pipeline.

### What is the "thin orchestrator" pattern?

Files in `scripts/` should not implement mathematical operations. They should:

- Import pure functions from `src/`.
- Run experiment loops (calling those functions).
- Delegate side-effects (file I/O, logging, progress bars) to `infrastructure/`.
- Write outputs to `output/`.

If you find yourself writing a gradient update or a quadratic evaluation
inside `scripts/`, move it to `src/` and add a test.

### Why are mocks forbidden?

Mocking tests that a function *was called* instead of that it produced
the *correct result*. Pure functions can be tested with real inputs and
expected outputs. Mocks give a false sense of correctness and break the
reproducibility guarantee.

## Testing and coverage

### Why 90% coverage? Can I lower it?

The coverage gate ensures `src/` logic is thoroughly exercised. Lowering
the gate compromises the exemplar's authority. If coverage drops, it
signals missing tests — add them, don't lower the gate.

### My new function lowered coverage. What now?

Write unit tests for the new function before or immediately after adding
it. Follow the existing test classes in `tests/test_optimizer.py`. Use
fixed arrays and assert mathematical properties (convergence, gradient
accuracy, shape checks).

### Do I need to test `scripts/`?

`scripts/` is tested via integration tests that run when `infrastructure`
is available. Those tests call the main function and assert it produces
output files. They are marked to skip gracefully if `infrastructure` is
not installed. See [`testing_philosophy.md`](testing_philosophy.md).

## Manuscript and rendering

### How do I add a new figure?

1. Add a generator function to `scripts/optimization_analysis.py` that
   writes a PNG to `output/figures/` with a fixed filename
   (e.g. `new_figure.png`).
2. In `manuscript/03_results.md`, add a Pandoc image line:
   ```markdown
   ![Caption text.](../output/figures/new_figure.png){#fig:new_label}
   ```
3. Reference it in prose using Pandoc-crossref:
   `See [@fig:new_label] for the result.`
4. Update [`syntax_guide.md`](syntax_guide.md) with the new figure label
   and generator.
5. Re-run the pipeline (analysis, variables, render).

### What are `{{VARIABLE}}` tokens and why use them?

Tokens inject dynamic values (config parameters, computed results) into
the manuscript without hard-coding. They keep the prose synchronized
with the analysis outputs. The variable generator
(`scripts/z_generate_manuscript_variables.py`) reads `config.yaml` and
result files, builds a `{TOKEN: value}` dictionary, and substitutes all
tokens in `output/manuscript/*.md` before rendering.

See [`syntax_guide.md`](syntax_guide.md) for the canonical token list.

### A token is not being resolved — `{{MY_TOKEN}}` appears in the PDF

See [`troubleshooting.md`](troubleshooting.md#literal-token_name-appears-in-the-rendered-pdf).

### Where does the rendered PDF live?

Working copy:
```
projects/template_code_project/output/pdf/template_code_project_combined.pdf
```

Promoted copy (used by CI for artifact upload):
```
output/template_code_project/template_code_project_combined.pdf
```

## Common pitfalls

### I imported `infrastructure` in `src/` and tests broke

Pure-math modules (`src/optimizer.py`, `src/invariants.py`) must stay infrastructure-free. Orchestration modules (`src/analysis.py`, `src/figures.py`, `src/dashboard.py`, `src/manuscript_variables.py`) may import `infrastructure.*` behind try/except fallbacks. If you added infrastructure to a math primitive, move that code to an orchestration module or `scripts/`.

### My test uses `unittest.mock` and coverage dropped

Replace the mock with real data. Mocks are forbidden. Write a test that
calls the actual function with a fixed `numpy` array and asserts the
mathematical result.

### I added a test and the count changed. Is that OK?

Yes. The count will vary as tests are added or removed. What matters is
**≥ 90% coverage** on `src/` and **all** tests passing.

### The analysis script runs but `output/figures/` is empty

Check that the script completed successfully (exit code 0). Look for
errors in the log or in `output/logs/pipeline.log`. Ensure you ran the
script with `uv run` from the repository root so imports resolve
correctly.

## See also

- [`quickstart.md`](quickstart.md) — basic commands.
- [`troubleshooting.md`](troubleshooting.md) — symptom-driven recipes.
- [`output_conventions.md`](output_conventions.md) — output regeneration rules.
- [`syntax_guide.md`](syntax_guide.md) — Pandoc-crossref syntax and token list.
- [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) — token protocol and figure list.
