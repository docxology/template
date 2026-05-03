# `template_prose_project/tests/`

Real-data test suite for the prose-review pipeline. **No mocks.**

## Run

```bash
# Full suite (37 tests, ~2 s)
uv run pytest projects/template_prose_project/tests/ -v

# Coverage gate
uv run pytest projects/template_prose_project/tests/ \
    --cov=projects/template_prose_project/src \
    --cov-fail-under=90
```

## Structure

| File | Tests |
|---|---|
| `test_config.py` | YAML loader: minimal, full, edge cases. |
| `test_pipeline.py` | `run_prose_pipeline` happy path + every check failure mode. |
| `test_pipeline_integration.py` | End-to-end against a copy of the bundled `manuscript/`. |
| `test_figures.py` | Matplotlib renderers; round-trip JSON loader. |
| `test_manuscript_variables.py` | `compute_variables`, `substitute_in_text`. |
| `test_report.py` | Markdown review-report assembly. |
| `test_scripts.py` | Real `subprocess.run` against the orchestrator scripts. |

## Conventions

* **No mocks.** Real prose, real BibTeX content, real `tmp_path`
  directories, real subprocess.
* **`tmp_path` for isolation.** Tests never touch the project's own
  `output/`.
* **90%+ coverage gate** (currently 98%+).

See [AGENTS.md](AGENTS.md) for the editing rules and how to add new tests.
