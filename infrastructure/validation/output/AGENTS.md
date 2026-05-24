# infrastructure/validation/output/ - Output Validation Documentation

## Purpose

The `infrastructure/validation/output/` package contains pipeline output validation and no-mock enforcement helpers.

## Files

- `validator.py` - output structure validation (`validate_copied_outputs`, `validate_output_structure`, …)
- `pipeline.py` - Stage 4 orchestration (`validate_pdfs`, `validate_manuscript_output_markdown`, `execute_validation_pipeline`)
- `no_mock_enforcer.py` - mock-usage checks (line-based scan; one-line `"""..."""` / `'''...'''` docstrings are skipped so policy docs can name forbidden APIs)

## Key APIs

### `pipeline.py`

- `validate_manuscript_output_markdown(project_name)` — pipeline wrapper; resolves `projects/{name}/manuscript/` and calls content `validate_markdown()`. **Not** the same symbol as content `validate_markdown(dir, repo_root)`.
- `validate_pdfs(project_name)` — PDF validation for project output dir
- `execute_validation_pipeline(project_name)` — runs PDF + markdown checks for Stage 4

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
- [`../content/discovery.py`](../content/discovery.py) — manuscript markdown enumeration (`scope="tree"`)
