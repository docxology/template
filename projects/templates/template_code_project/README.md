# Code Project — Optimization Research Exemplar

Research project demonstrating optimization algorithms with automated figure generation and publication-quality output. Exemplar roster: [`projects/AGENTS.md`](../../AGENTS.md#permanent-canonical-exemplars-and-optional-search-add-on).

## Run via the template monorepo

This exemplar lives at `projects/templates/template_code_project/` in the public
[docxology/template](https://github.com/docxology/template) repository.
**Tests, analysis, PDF rendering, and CI all run through that monorepo** —
clone it, run `uv sync` at the repository root, then:

```bash
./run.sh --project templates/template_code_project --pipeline --core-only
# or: uv run python scripts/execute_pipeline.py --project templates/template_code_project --core-only
```

Several exemplars also publish standalone GitHub/Zenodo releases for citation;
those mirrors are outputs of this pipeline. The monorepo remains the canonical
build and render surface.

## When to use this template

Use this template for **code-driven computational research**: algorithms in
`src/`, numerical experiments with deterministic seeds, automated
publication-quality figures, and a manuscript that reports the computed
results. It is the flagship demonstration of the thin-orchestrator pattern
(scripts coordinate; `src/` implements; tests enforce ≥90% coverage with no
mocks). If your project is primarily prose review, layout, or book-length
structure, see [`template_prose_project`](../template_prose_project/),
[`template_newspaper`](../template_newspaper/), or
[`template_textbook`](../template_textbook/) instead.

## Quick Start

```bash
# Run the analysis pipeline
uv run python projects/templates/template_code_project/scripts/optimization_analysis.py

# Run tests
uv run pytest projects/templates/template_code_project/tests/ -v

# View final deliverables (after scripts/05_copy_outputs.py)
ls -la output/template_code_project/
```

## Prerequisites & verification

**Test/coverage gate (authoritative per-project command).** Exit code 0
alone is not proof — confirm tests collected > 0 and coverage ≥ 90%:

```bash
uv run pytest projects/templates/template_code_project/tests/ \
  --cov=projects/templates/template_code_project/src --cov-fail-under=90
# live baseline: docs/_generated/COUNTS.md
```

**Combined-PDF rendering & Mermaid.** This project's convention is
Mermaid-for-all-diagrams. If a manuscript section embeds a ```mermaid```
block, the combined PDF is built with `mmdc`, which needs a pinned
`chrome-headless-shell` (CI provisions it; a fresh clone does not):

```bash
npx --yes puppeteer browsers install chrome-headless-shell
```

Without it the **PDF Rendering** stage fails while slides still render — see
[`docs/troubleshooting.md`](docs/troubleshooting.md#pdf-rendering-fails-mmdc-could-not-find-chrome).
Full end-to-end: `uv run python scripts/execute_pipeline.py --project template_code_project --core-only`.

## Dependencies

Run `uv sync` at the **repository root**; that environment is what CI and `./run.sh` use. [`pyproject.toml`](pyproject.toml) in this directory configures pytest/coverage for `projects/templates/template_code_project/tests/` and records the same scientific stack for isolated runs. Root [`pyproject.toml`](../../../pyproject.toml) has `[tool.uv.workspace]` with `members = []`, so this folder is not installed as a separate workspace package.

## Agentic research overlays

This exemplar includes two declarative overlays for advisory research controls:

- [`domain_profile.yaml`](domain_profile.yaml) declares the code-research domain,
  expected outputs, review gates, source policy, artifact expectations, and
  benchmark rubric weights.
- [`experiment_plan.yaml`](experiment_plan.yaml) declares the deterministic
  gradient-descent conditions, primary metric direction, expected figures and
  tables, baseline, and ablation condition.
- [`data/claim_ledger.yaml`](data/claim_ledger.yaml) registers manuscript
  numeric claims that are intentionally sourced from project code, captions, or
  generated artifacts rather than `{{TOKEN}}` variables.

These files are validation and benchmark inputs only. They do not fork project
trees, mutate prompts, or run autonomous experiment agents.

## Why this template — the transferable pattern

The genuinely transferable lesson is not gradient descent. It is
**reproducibility-by-construction**: every numeric in the manuscript prose
is a `{{TOKEN}}` registered in one Python function
(`src/manuscript_variables.py::generate_variables`) and cross-checked by
one test (`tests/test_manuscript_variables.py::test_all_manuscript_tokens_are_generated`),
which fails CI on any token used in prose that the generator does not emit.
The deliverable PDF is therefore *proof* that the repo's invariants held
during build: configuration drift, deleted result, or out-of-sync narrative
cannot reach a green PDF without the gate flipping red first. A forker who
internalizes "every prose number is a token, every token is a single Python
function, every drift is a CI failure" gets that discipline for free —
regardless of whether their domain is optimization.

## Key Features

- **Gradient descent optimization** with convergence analysis
- **Automated figure generation** (convergence plots, stability analysis, performance benchmarks)
- **Scientific validation** (numerical stability assessment, performance benchmarking)
- **Comprehensive reporting** (HTML dashboard with analysis metrics)
- **Performance monitoring** (resource usage tracking with progress indicators)
- **Data export** (optimization results, analysis reports, performance metrics)
- **Manuscript integration** (figure registration and cross-referencing)

## Common Commands

### Run Analysis

```bash
uv run python projects/templates/template_code_project/scripts/optimization_analysis.py
```

Generates convergence plots, performs scientific validation, creates dashboard, and saves all results.

### Run Tests

```bash
uv run pytest projects/templates/template_code_project/tests/ -v
```

Tests optimization algorithms and numerical accuracy.

### View Results

```bash
open projects/templates/template_code_project/output/figures/convergence_plot.png
cat projects/templates/template_code_project/output/data/optimization_results.csv
```

## Architecture

```mermaid
graph TD
    A[scripts/optimization_analysis.py] --> B[src/analysis/]
    B --> C[src/optimizer.py]
    B --> D[Scientific Analysis]
    B --> E[Generate Figures]
    B --> F[Export Data]
    B --> G[Create Dashboard]

    AA[scripts/generate_api_docs.py] --> AB[API Documentation]
    AA --> AC[Code Quality Report]

    C --> H[Gradient Descent]
    C --> I[Quadratic Functions]
    C --> J[Convergence Analysis]

    D --> K[Stability Assessment]
    D --> L[Performance Benchmarking]
    D --> M[Progress Monitoring]

    E --> N[Convergence Plots]
    E --> O[Stability Visualizations]
    E --> P[Benchmark Charts]

    G --> Q[HTML Dashboard]
    G --> R[Analysis Reports]

    F --> S[CSV Results]
    F --> T[JSON Reports]
```

## .cursorrules Compliance

✅ **Fully compliant** with template development standards:

- **Testing**: `src/` coverage is gated at 90%; live test count + achieved coverage tracked in [`../../docs/_generated/COUNTS.md`](../../../docs/_generated/COUNTS.md)
- **Documentation**: AGENTS.md + README.md in each directory
- **Type Safety**: Full type hints on all public APIs
- **Code Quality**: Ruff format/check (CI parity), descriptive naming, proper imports
- **Error Handling**: Context preservation, informative messages
- **Logging**: Unified logging system throughout

## Manuscript authoring

When editing manuscript markdown:

- [`manuscript/SYNTAX.md`](manuscript/SYNTAX.md) — citation, equation, figure, table, and section conventions specific to this project (label registries for all 6 figures and 8 equations).
- [`../../docs/guides/manuscript-semantics.md`](../../../docs/guides/manuscript-semantics.md) — repository-wide manuscript semantics.
- [`manuscript/AGENTS.md`](manuscript/AGENTS.md) — `{{TOKEN}}` substitution protocol and section-modification workflow.

## More Information

See [AGENTS.md](AGENTS.md) for technical documentation.

## Template integrity

- Forward backlog: [`TODO.md`](TODO.md).
- Copy-and-customize config: [`manuscript/config.yaml.example`](manuscript/config.yaml.example).
- Project validation: `uv run pytest projects/templates/template_code_project/tests/ --cov=projects/templates/template_code_project/src --cov-fail-under=90`.
- Repo drift validation: `uv run python scripts/check_template_drift.py --strict`.
