---
title: "Manuscript directory: code_project"
type: "manuscript_guide"
version: "2.2"
---

# Manuscript (`projects/code_project/manuscript/`)

Repository-wide agent rules for this exemplar live in [`../docs/agent_instructions.md`](../docs/agent_instructions.md). This file covers **manuscript-specific** editing: file roles, `{{VARIABLE}}` token protocol, figure protocol, and the section modification workflow.

## File Inventory

| File / Pattern | Role | `{{VARIABLE}}` Tokens | Figure References |
|---|---|---|---|
| `00_abstract.md` | Abstract; introduces template features and results summary | `CONFIG_NUM_STEP_SIZES`, `CONFIG_MIN_STEP_SIZE`, `CONFIG_MAX_STEP_SIZE`, `CONFIG_MAX_ITERATIONS`, `RESULT_NUM_CONVERGED`, `RESULT_OPTIMUM_X`, `RESULT_OPTIMUM_F` | None |
| `01_introduction.md` | Infrastructure pillars, algorithm overview, reader's guide | None | None |
| `02_methodology.md` | Mathematical methods, gradient descent algorithm, step-size theory | `CONFIG_STEP_SIZES_BULLETS` | None |
| `03_results.md` | All results; ALL figures; ALL numeric result tokens | `CONFIG_STEP_SIZES_CSV`, `CONFIG_MAX_ITERATIONS`, `CONFIG_TOLERANCE`, `CONFIG_CONVERGENCE_TOL`, `CONFIG_NUM_STEP_SIZES`, `CONFIG_NUM_STABILITY_STARTS`, `CONFIG_NUM_STABILITY_STEPS`, `CONFIG_STABILITY_CELLS`, `CONFIG_STABILITY_MIN_STEP`, `CONFIG_STABILITY_MAX_STEP`, `CONFIG_BENCHMARK_DIMS`, `RESULT_OPTIMUM_F`, `RESULT_MIN_ITERATIONS`, `RESULT_MAX_ITERATIONS`, `RESULT_AVG_ITERATIONS`, `RESULT_BEST_STEP_SIZE`, `RESULT_NUM_CONVERGED`, `RESULT_OPTIMUM_X`, `RESULT_TABLE_ROWS`, `RESULT_CONVERGENCE_FACTORS`, `STABILITY_SCORE` | All 6 figures |
| `04_conclusion.md` | Summary of pipeline automation and template guarantees | None | None |
| `05_experimental_setup.md` | Configuration parameters, software environment | `CONFIG_QUADRATIC_A`, `CONFIG_QUADRATIC_B`, `RESULT_OPTIMUM_X`, `RESULT_OPTIMUM_F`, `CONFIG_NUM_STEP_SIZES`, `CONFIG_STEP_SIZES_BULLETS`, `CONFIG_INITIAL_POINT`, `CONFIG_CONVERGENCE_TOL`, `CONFIG_MAX_ITERATIONS`, `CONFIG_NUM_STABILITY_STARTS`, `CONFIG_NUM_STABILITY_STEPS`, `CONFIG_STABILITY_CELLS`, `CONFIG_BENCHMARK_DIMS`, `CONFIG_BENCHMARK_MIN_DIM`, `CONFIG_BENCHMARK_MAX_DIM`, `PYTHON_VERSION`, `NUMPY_VERSION`, `PLATFORM`, `GENERATION_TIMESTAMP` | None |
| `06_reproducibility.md` | Config hash, artifact inventory, test results | `CONFIG_HASH`, `CONFIG_VERSION`, `CONFIG_FIRST_AUTHOR`, `CONFIG_KEYWORDS`, `ARTIFACT_FIGURES`, `ARTIFACT_DATA_FILES` | None |
| `07_scope_and_related_work.md` | Scope limitations, related literature | None | None |
| `config.yaml` | Paper metadata and all experiment parameters | — | — |
| `config.yaml.example` | Reference copy for new projects; shows all configurable fields | — | — |
| `preamble.md` | LaTeX injections shared by PDF output | — | — |
| `references.bib` | BibTeX bibliography | — | — |
| `SYNTAX.md` | Citation, figure, and cross-reference syntax reference | — | — |
| `README.md` | Human quick-reference for this directory | — | — |
| `AGENTS.md` | This file — agent technical directives | — | — |

## {{VARIABLE}} Protocol

Numeric values that come from analysis outputs **must** use `{{VARIABLE_NAME}}` syntax. Hardcoding a number that will change when `config.yaml` is edited or the analysis is re-run is the primary cause of inaccurate manuscripts.

**The token pipeline**:
1. `scripts/z_generate_manuscript_variables.py` reads `config.yaml` and `output/data/optimization_results.csv`
2. It builds a `{TOKEN: value}` dict and writes it to `output/data/manuscript_variables.json`
3. It copies each `manuscript/*.md` template to `output/manuscript/*.md`, substituting every `{{TOKEN}}` with its resolved value
4. `scripts/03_render_pdf.py` renders the **substituted** copies (from `output/manuscript/`), not the originals

**Adding a new token**:
1. Add a key/value pair to the `variables` dict in `z_generate_manuscript_variables.py::build_variables()`
2. Verify: `python -c "import json; d=json.load(open('projects/code_project/output/data/manuscript_variables.json')); print(d['MY_TOKEN'])"`
3. Reference in a manuscript file as `{{MY_TOKEN}}`

**Detecting unresolved tokens** (run before rendering):
```bash
grep -r "{{" projects/code_project/output/manuscript/ 2>/dev/null \
  && echo "UNRESOLVED TOKENS — re-run z_generate_manuscript_variables.py" \
  || echo "All tokens resolved"
```

See [`../docs/syntax_guide.md`](../docs/syntax_guide.md) for the complete token reference table (28 tokens).

## Figure Protocol

All six figures must be referenced via `\ref{}`, never with hardcoded numbers:

| Label | PNG Filename | Generator Function in `scripts/optimization_analysis.py` |
|---|---|---|
| `{#fig:convergence}` | `output/figures/convergence_plot.png` | `generate_convergence_plot()` |
| `{#fig:step_sensitivity}` | `output/figures/step_size_sensitivity.png` | `generate_step_size_sensitivity_plot()` |
| `{#fig:convergence_rate}` | `output/figures/convergence_rate_comparison.png` | `generate_convergence_rate_plot()` |
| `{#fig:complexity}` | `output/figures/algorithm_complexity.png` | `generate_algorithm_complexity_plot()` |
| `{#fig:benchmark}` | `output/figures/performance_benchmark.png` | `generate_benchmark_visualization()` |
| `{#fig:stability}` | `output/figures/stability_analysis.png` | `generate_stability_visualization()` |

**To add a new figure**:
1. Add a generator function to `scripts/optimization_analysis.py` that writes a new PNG under `projects/code_project/output/figures/`.
2. In the appropriate manuscript section, add a Pandoc image line (alt, relative path under `../output/figures/`, and `{#fig:…}`) by copying the structure of any figure in `03_results.md` and updating the path to match the file your generator writes.
3. Reference in prose: `Figure \ref{fig:new_label}`
4. Document in `output/AGENTS.md` regeneration table

## Infrastructure Coupling (`scripts/`, not `src/`)

Orchestrators under `projects/code_project/scripts/` should use `infrastructure.core.logging.utils.get_logger(__name__)` (same pattern as `optimization_analysis.py`). Scientific checks should go through `infrastructure.scientific` helpers where applicable. `src/optimizer.py` must remain infrastructure-free.

## Section Modification Protocol

Follow these steps in order whenever you change behavior and need to update the manuscript:

1. **Update mathematical or experimental description** in `02_methodology.md` / `05_experimental_setup.md` as needed.
2. **Add or extend tests** in `projects/code_project/tests/test_optimizer.py` (there is no separate `tests/integration/` tree in this project).
3. **Regenerate analysis outputs**:
   ```bash
   uv run python projects/code_project/scripts/optimization_analysis.py
   ```
4. **Hydrate manuscript variables** (substitute `{{VARIABLE}}` tokens):
   ```bash
   uv run python projects/code_project/scripts/z_generate_manuscript_variables.py
   ```
5. **Verify all tokens resolved**:
   ```bash
   grep -r "{{" projects/code_project/output/manuscript/ || echo "All resolved"
   ```
6. **Render PDF** from the repository root:
   ```bash
   uv run python scripts/03_render_pdf.py --project code_project
   ```
7. **Verify figures and table appear** in the rendered PDF; check `output/tex/*.log` for LaTeX errors.

Final deliverables appear under `output/code_project/` after `scripts/05_copy_outputs.py` runs (working files remain under `projects/code_project/output/` during the run).

## RASP Conventions

1. Avoid boilerplate closers such as "In summary" / "In conclusion" at the end of sections unless the section genuinely needs them.
2. Figures and numbers in `03_results.md` must match what `scripts/optimization_analysis.py` writes (paths under `projects/code_project/output/figures/` and related CSV/JSON).
3. When referencing template code, prefer concrete paths or URLs (e.g. [core utilities in the template repository](https://github.com/docxology/template/tree/main/infrastructure/core)) over vague module dotted paths alone.

## See also

- [`README.md`](README.md) — Quick orientation
- [`SYNTAX.md`](SYNTAX.md) — Pandoc syntax reference for this manuscript
- [`../docs/rendering_pipeline.md`](../docs/rendering_pipeline.md) — Manuscript → PDF flow (4 phases)
- [`../docs/syntax_guide.md`](../docs/syntax_guide.md) — Complete `{{VARIABLE}}` token reference
- [`../scripts/z_generate_manuscript_variables.py`](../scripts/z_generate_manuscript_variables.py) — Variable hydration script
