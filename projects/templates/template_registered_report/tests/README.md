# tests - template_registered_report

Real-data, no-mock tests across four files:

- `test_protocol.py` — registration freezing, section validation, deviation
  classification, sensitivity-table checks, review packets, and analysis-plan
  drift; plus prose-binding tests for the manuscript's sensitivity row and
  deviation ledger, and a test that the committed review artifacts under
  `output/reports/` equal a fresh deterministic regeneration.
- `test_demo_study.py` — the deterministic demonstration study, grouped into
  `TestDemoDataset`, `TestPermutationTest`, `TestRegisteredAnalysis`, and
  `TestDiagramData`. These pin the seeded statistics the manuscript quotes and
  assert the executed summary matches the committed
  `output/data/demo_analysis.json` artifact when present.
- `test_figures.py` — deterministic figure rendering: each plot writes a real,
  non-empty PNG, and `render_all_figures` is byte-stable across runs.
- `test_generate_figures_script.py` — script-level integration: asset
  generation writes a validator-compatible registry, an incomplete render set
  cannot publish a registry, and the validator rejects a deleted registered
  figure.

Run from the repository root:

```bash
uv run pytest projects/templates/template_registered_report/tests --cov=projects/templates/template_registered_report/src --cov-fail-under=90
```
