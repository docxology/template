# Quickstart

## Prerequisites

For an independent checkout, use the genuine SDK-wheel recipe in
[README.md](../README.md#standalone-repository-project-root).
For a canonical checkout, prepare Root and this project's own environment through
the [shared run surface](https://github.com/docxology/template/blob/main/projects/README.md#run-surface),
then enter `projects/templates/template_gold_refinement/`.
The local commands below run from the prepared project root; initial dependency
preparation may need package access, while these local artifacts require no
publication credentials.

## First local artifacts and manuscript hydration

```bash
# 1. Run the analysis (generates refinery data, token plan, figures)
.venv/bin/python scripts/refinement_analysis.py

# 2. Generate manuscript variables (substitutes {{TOKEN}} placeholders)
.venv/bin/python scripts/z_generate_manuscript_variables.py
```

## Full pipeline (from repo root)

Return to the prepared monorepo root; repository stage scripts are not supplied
by an independent project. See the
[dispatch guide](https://github.com/docxology/template/blob/main/docs/RUN_GUIDE.md).

```bash
./run.sh --project templates/template_gold_refinement --pipeline --mode core
```

## Expected local outputs

- `output/data/refinery_results.json` — refinery demonstration results.
- `output/reports/token_plan.json` — configured token plan.
- `output/data/manuscript_variables.json` — variables for manuscript hydration.
- `output/manuscript/` — the hydrated manuscript tree.

Inspect the actual files and command exits. Missing/unreadable output is not
successful validation; a text search alone does not prove manuscript or PDF
correctness. These analogy artifacts are not physical/metallurgical findings,
native-format acceptance or publication acceptance. Preserve retained public
outputs and immutable evidence; generated does not mean disposable.

## Coverage gate

Use the complete own-suite and branch-coverage commands in the
[standalone recipe](../README.md#standalone-repository-project-root).
They retain the declared coverage floor and are separate from the first local
artifact run; no successful execution or fixed duration is claimed here.
