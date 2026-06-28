# infrastructure/validation/output/ - Output Validation Documentation

## Purpose

The `infrastructure/validation/output/` package contains pipeline output validation and no-mock enforcement helpers.

## Files

- `validator.py` - output structure validation (`validate_copied_outputs`, `validate_output_structure`, ...)
- `pipeline.py` - Stage 4 orchestration facade (`validate_pdfs`, `validate_manuscript_output_markdown`, `execute_validation_pipeline`)
- `pdf_checks.py` - PDF structure and transmission bookend checks
- `markdown_checks.py` - manuscript markdown wrapper and diagnostic report handling
- `design.py` - domain profile, experiment plan, and AutoResearch overlay validation
- `artifacts.py` - artifact manifest JSON parsing and current-manifest selection
- `prose_quality.py` - opt-in, report-only AI-writing prose quality gate
- `claim_verification.py` - optional web-grounded claim verification report for manuscript prose
- `no_mock_enforcer.py` - mock-usage checks (line-based scan; one-line `"""..."""` / `'''...'''` docstrings are skipped so policy docs can name forbidden APIs)

## Key APIs

### `pipeline.py`

- `validate_manuscript_output_markdown(project_name)` — pipeline wrapper; resolves `projects/{name}/manuscript/` and calls content `validate_markdown()`. **Not** the same symbol as content `validate_markdown(dir, repo_root)`.
- `validate_pdfs(project_name)` — PDF validation for project output dir
- `execute_validation_pipeline(project_name)` — runs PDF + markdown checks for Stage 4
- `validate_claim_verification(project_root)` — optional report-only web claim verification over manuscript Markdown

## See Also

- [`README.md`](README.md)
- [`../AGENTS.md`](../AGENTS.md)
- [`../content/discovery.py`](../content/discovery.py) — manuscript markdown enumeration (`scope="tree"`)
