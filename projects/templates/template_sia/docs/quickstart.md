# Quickstart — template_sia

## From repository root

```bash
# Tests
uv run python scripts/pipeline/stage_01_test.py --project templates/template_sia --project-only

# Analysis only
uv run python scripts/pipeline/stage_02_analysis.py --project templates/template_sia

# Core pipeline (tests → analysis → PDF → validate → copy)
uv run python scripts/runner/execute_pipeline.py --project templates/template_sia --core-only --skip-infra
```

## From project directory

```bash
cd projects/templates/template_sia
uv run python scripts/run_sia_loop.py
uv run python scripts/z_generate_manuscript_variables.py
```

## Bounded live numeric proposals (optional)

With Docker, an immutable local Python image ID, and the selected model already
available from a loopback Ollama service:

```bash
uv run python scripts/run_sia_loop.py --live-proposals \
  --model <local-model-name> --container-image sha256:<existing-local-image-id> \
  --proposal-output-dir output/live_proposals_example
```

The CLI model overrides `project_config.sia.llm_model`; the shipped empty value
requires an explicit selection. No tool, image, or model is downloaded by the
command. Missing capabilities block with exit 75. The target runs only in the
restricted Docker container. Its numeric mutation scope, exact rollback,
held-out boundary, and receipt files are described in
[`live-numeric-proposals.md`](live-numeric-proposals.md).

`--live-sia` executes unchanged reference subprocess diagnostics. Its optional
feedback note supplies no mutation or sandbox acceptance.

Default pipeline and CI use fixture replay (`live: false` in `manuscript/config.yaml`).

## Deliverables

- Combined PDF: `output/templates/template_sia/pdf/template_sia_combined.pdf`
- Loop report: `projects/templates/template_sia/output/reports/sia_loop_report.md`
