# template_autoresearch_project - Agent Notes

## Purpose

This project is the public exemplar for deterministic AutoResearch loops in
`template/`. It should remain small, auditable, and runnable through `run.sh`.

## Architecture

- Business logic: `src/`
  - `loop.py` — thin orchestrator (`run_autoresearch_loop`)
  - `models.py` — loop result dataclasses
  - `config.py` — manuscript settings + plan merge (`build_loop_config`)
  - `writers.py` — JSON/CSV/manifest I/O
  - `reports.py` — markdown and review-packet renderers
  - `figures.py` — stage matrix figure + registry metadata
  - `manuscript_variables.py` — render-time token hydration
- Thin scripts: `scripts/`
- Project docs: `docs/`
- Manuscript source: `manuscript/`
- Generated artifacts: `output/`

The analysis stage must not perform network calls, LLM calls, generated-code
execution, or autonomous approval. It composes existing infrastructure modules:

- `infrastructure.autoresearch`
- `infrastructure.validation.evidence_registry`
- `infrastructure.core.pipeline.artifacts`
- `infrastructure.rendering.manuscript_injection`

## Loop flow

1. `build_autoresearch_plan()` — canonical topic, artifacts, and quality checks
2. `validate_autoresearch_plan(..., phase="intrinsic")` — domain, experiment, pipeline, scripts
3. `write_core_loop_artifacts()` — plan, loop markdown, stage matrix CSV, figure
4. `validate_autoresearch_plan(..., phase="extrinsic")` — evidence registry and artifact manifest
5. `write_autoresearch_report()` — combined intrinsic + extrinsic readiness
6. `finalize_loop_payloads()` — loop JSON, claims, review packet, summary, variables

Loop stages use status `declared` (intent only — not pipeline execution proof).
Claims are `supported` only when the configured evidence path exists on disk.

## Run Commands

```bash
./run.sh --pipeline --project template_autoresearch_project --core-only --skip-infra
uv run python scripts/01_run_tests.py --project template_autoresearch_project --project-only
uv run python -m infrastructure.autoresearch.cli validate --project template_autoresearch_project --fail-on-issues
```

## Editing Rules

- Keep `scripts/` as orchestrators only.
- Add orchestration in `src/loop.py`; add I/O in `src/writers.py`; add renderers in `src/reports.py`.
- Add manuscript tokens through `src/manuscript_variables.py` and tests.
- Keep `autoresearch.yaml` stage names exact against `pipeline.yaml`.
- Update `docs/` when changing configurable methods or output contracts.
