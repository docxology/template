# tests - AGENTS.md

Real-data, no-mock suite. Use real registration dictionaries and fixture files;
never mock the validators, the demonstration analysis, or the figure renderers.

- `test_protocol.py` — registration freezing, required-section validation,
  duplicate-hypothesis and outcome checks, deviation classification,
  sensitivity-table validation, and review packets.
- `test_demo_study.py` — the deterministic demonstration study (dataset,
  permutation test, plan-driven analysis binding, diagram-data helpers, and
  manuscript-prose binding against live analysis numbers).
- `test_figures.py` — deterministic figure rendering (each plot writes a real
  PNG) and byte-stability across runs.
- `test_generate_figures_script.py` — script-level asset generation, figure
  registry publication provenance, and validator rejection of incomplete or
  deleted registered figures.

Run one project directory per pytest invocation from the repository root:

```bash
uv run pytest projects/templates/template_registered_report/tests --cov=projects/templates/template_registered_report/src --cov-fail-under=90
```
