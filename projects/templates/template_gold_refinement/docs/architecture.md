# Architecture

## Overview

The gold-refinement exemplar follows the template's two-layer architecture:

- **Layer 1** (`infrastructure/`): Generic build, validation, and rendering tools
- **Layer 2** (this project): Domain-specific refinery logic and mega-madlib composition

## Module dependencies

```
refinery.py ← purity.py
    ↑
config.py ← composition.py
    ↑
manuscript_variables.py
    ↑
scripts/z_generate_manuscript_variables.py
```

The core chain above covers token composition and manuscript variables. A
second, parallel layer covers scientific integrity, security, and delivery:

```
integrity.py ← formalisms.py
    ↑
assay.py ← evidence.py (claim-vs-evidence checks; evidence.py also
    │        cross-checks contribution claims against source files)
    ↑
domain_adapter.py (remaps domain-specific metrics onto the purity scale)

coercion.py, parsing.py ← pipeline_policy.py (steganography + LLM review
    gating) and domain_adapter.py (shared helpers)

security_assay.py → dashboard.py (interactive HTML dashboard)
cover_visualization.py (matplotlib cover composite)
```

`src/figures/` is a 5-module package (`_common.py`, `charts.py`,
`diagrams.py`, `graphs.py`, `registry.py`) behind the single
`FIGURE_SPECS` registry; see `docs/syntax_guide.md` for the full
per-figure inventory.

## Data flow

1. `manuscript/config.yaml` (gold_refinement block) → `config.py::load_gold_refinement_config()`
2. `config.py` → `composition.py::generate_token_plan()` → TokenPlan
3. `refinery.py::run_refinery()` → RefineryResult (5 stages with monotonicity, order, and adjacent-continuity guards)
4. `refinery.py::stages_to_target()` → shortest ordered prefix reaching a declared target; `purity.py::PurityVector` → noncompensatory quality dimensions
5. `figures/registry.py::generate_all_figures()` → PNG + SVG files, `figure_registry.json`, `figure_quality_report.json`
6. `assay.py::assay_claims()` and `evidence.py::build_evidence_registry()` → claim-support and evidence registries
7. `dashboard.py::write_dashboard()` → `output/dashboard.html`
8. `manuscript_variables.py::generate_variables()` → flat dict of {{TOKEN}} values
9. `infrastructure.rendering.manuscript_injection.write_resolved_manuscript_tree()` → output/manuscript/
10. `infrastructure.rendering.pdf_renderer` → PDF

## Layer contract

`src/` must not import `infrastructure.*`. All infrastructure coupling belongs in `scripts/`.
