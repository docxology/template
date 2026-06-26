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

## Data flow

1. `manuscript/config.yaml` (gold_refinement block) → `config.py::load_gold_refinement_config()`
2. `config.py` → `composition.py::generate_token_plan()` → TokenPlan
3. `refinery.py::run_refinery()` → RefineryResult (5 stages, monotone purity)
4. `figures.py::generate_all_figures()` → PNG files + figure_registry.json
5. `manuscript_variables.py::generate_variables()` → flat dict of {{TOKEN}} values
6. `infrastructure.rendering.manuscript_injection.write_resolved_manuscript_tree()` → output/manuscript/
7. `infrastructure.rendering.pdf_renderer` → PDF

## Layer contract

`src/` must not import `infrastructure.*`. All infrastructure coupling belongs in `scripts/`.
