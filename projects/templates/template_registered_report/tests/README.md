# tests - template_registered_report

Real-data, no-mock tests across two files:

- `test_protocol.py` — registration freezing, section validation, deviation
  classification, sensitivity-table checks, review packets, and analysis-plan
  drift.
- `test_demo_study.py` — the deterministic demonstration study, grouped into
  `TestDemoDataset`, `TestPermutationTest`, `TestRegisteredAnalysis`, and
  `TestDiagramData`. These pin the seeded statistics the manuscript quotes and
  assert the executed summary matches the committed
  `output/data/demo_analysis.json` artifact when present.

Run from the repository root:

```bash
uv run pytest projects/templates/template_registered_report/tests --cov=projects/templates/template_registered_report/src --cov-fail-under=90
```
