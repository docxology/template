# Quickstart

## Prerequisites

```bash
# From the repository root
uv sync
```

## Run the refinery pipeline

```bash
# 1. Run the analysis (generates refinery data, token plan, figures)
uv run python projects/templates/template_gold_refinement/scripts/refinement_analysis.py

# 2. Generate manuscript variables (substitutes {{TOKEN}} placeholders)
uv run python projects/templates/template_gold_refinement/scripts/z_generate_manuscript_variables.py

# 3. Run tests
uv run pytest projects/templates/template_gold_refinement/tests/ -v
```

## Full pipeline (from repo root)

```bash
./run.sh --project templates/template_gold_refinement --pipeline --core-only
```

## Verify outputs

```bash
# Check refinery results
cat projects/templates/template_gold_refinement/output/data/refinery_results.json | python -m json.tool

# Check manuscript variables
cat projects/templates/template_gold_refinement/output/data/manuscript_variables.json | python -m json.tool

# Verify no unresolved tokens
grep -r "{{" projects/templates/template_gold_refinement/output/manuscript/ || echo "All resolved"
```

## Coverage gate

```bash
uv run pytest projects/templates/template_gold_refinement/tests/ \
  --cov=projects/templates/template_gold_refinement/src --cov-fail-under=90
```
