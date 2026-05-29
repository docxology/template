# tests/ - Agent Notes

## Purpose

This directory validates the deterministic AutoResearch exemplar with real
configuration, loop, artifact, and script execution paths.

## Scope

- `test_config.py` — manuscript settings, plan merge, and `parse_string_sequence`
- `test_loop.py` — file-backed loop orchestration, declared stage status, clean
  scaffold run against the real template repo root
- `test_reports.py` — markdown/CSV renderers and basic writer helpers
- `test_writers.py` — `write_loop_payloads()` core + finalize wrapper
- `test_manuscript_variables.py` — manuscript token hydration from loop outputs
- `test_manuscript_tables.py` — registry-backed table builders
- `test_figures.py` — figure registry and ML figure writers
- `test_gate_negative_controls.py` — substance-binding negative controls for claims/benchmarks
- `test_ml_task.py` — bounded ML task orchestration
- `test_scripts.py` — thin script smoke tests

## Commands

```bash
uv run python scripts/01_run_tests.py --project template_autoresearch_project --project-only
uv run pytest projects/template_autoresearch_project/tests/ -q
```

## Editing Rules

- Keep tests deterministic and local-only.
- Do not add network, LLM, generated-code execution, or autonomous approval
  dependencies.
- Prefer exercising real project files over mocked objects.
- Use `tmp_path` scaffolds with `repo_root=Path(__file__).resolve().parents[4]`
  when the test needs infrastructure `pipeline.yaml` without copying the full
  repository. (`parents[4]` because this exemplar lives at
  `projects/templates/<name>/tests/`; the `projects/templates/` lifecycle layout
  adds one level over the legacy `projects/<name>/` path.)
