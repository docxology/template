# template_search_project/tests — Agent guide

## Purpose

Offline, no-mocks coverage of `src/`: config, pipeline (local backend + temp dirs), synthesis, report, figures, manuscript variables, and script smoke paths. Infrastructure HTTP behaviour is covered in `tests/infra_tests/`; this suite focuses on project orchestration.

## Running

From repository root:

```bash
uv run pytest projects/templates/template_search_project/tests/ \
  --cov=projects/templates/template_search_project/src \
  --cov-fail-under=90
```

Project-local `pyproject.toml` sets `fail_under = 90` for coverage reports when run with `--cov` from this directory context.

## Conventions

- Use `tmp_path`, real JSON/corpus snippets, and deterministic LLM callables.
- Subprocess tests invoke `projects/templates/template_search_project/scripts/*.py` with explicit `--project-root` when isolating outputs.

## See also

- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)
