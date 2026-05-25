# tests/ - Agent Notes

## Purpose

This directory validates the deterministic AutoResearch exemplar with real
configuration, loop, artifact, and script execution paths.

## Scope

- `test_config.py` — manuscript settings, plan merge, and `parse_string_sequence`
- `test_loop.py` — file-backed loop orchestration, declared stage status, clean
  scaffold run against the real template repo root
- `test_reports.py` — markdown/CSV renderers and writer helpers
- `test_manuscript_variables.py` — manuscript token hydration from loop outputs
- `test_models.py` — result dataclass serialization
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
- Use `tmp_path` scaffolds with `repo_root=Path(__file__).resolve().parents[3]`
  when the test needs infrastructure `pipeline.yaml` without copying the full
  repository.
