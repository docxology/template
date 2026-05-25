# template_autoresearch_project

Public exemplar for the deterministic AutoResearch workflow.

This project demonstrates a file-backed AutoResearch loop that runs inside the
normal template pipeline:

```bash
./run.sh --pipeline --project template_autoresearch_project --core-only --skip-infra
```

The analysis stage runs two thin scripts:

- `scripts/run_autoresearch_loop.py` builds the plan, claims, stage matrix,
  review packet, evidence registry snapshot, artifact manifest, and readiness
  report through `src.loop.run_autoresearch_loop`.
- `scripts/z_generate_manuscript_variables.py` hydrates manuscript variables
  into `output/manuscript/` for rendering.

Reusable behavior lives under `src/` (`loop`, `models`, `config`, `writers`,
`reports`, `figures`, `manuscript_variables`). No network calls, LLM calls,
generated-code execution, or autonomous approval loops are used.

Loop stages are recorded as **declared** (configured intent). Claims are
**supported** only when their evidence file exists locally.

Project-specific docs live in [`docs/`](docs/).

## Outputs

- `output/data/autoresearch_plan.json`
- `output/data/autoresearch_loop.json`
- `output/data/autoresearch_claims.json`
- `output/data/autoresearch_stage_matrix.csv`
- `output/data/autoresearch_review_packet.json`
- `output/data/manuscript_variables.json`
- `output/figures/autoresearch_stage_matrix.png`
- `output/figures/figure_registry.json`
- `output/reports/autoresearch_loop.json`
- `output/reports/autoresearch_loop.md`
- `output/reports/autoresearch_review_packet.md`
- `output/reports/autoresearch_summary.md`
- `output/reports/autoresearch_readiness.json`
- `output/reports/autoresearch_readiness.md`
- `output/reports/evidence_registry.json`
- `output/reports/artifact_manifest.json`

## Tests

```bash
uv run python scripts/01_run_tests.py --project template_autoresearch_project --project-only --quiet
```
