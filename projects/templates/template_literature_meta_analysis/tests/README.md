# Tests - Literature Meta-Analysis

Run from the template repository root:

```bash
uv run pytest projects/templates/template_literature_meta_analysis/tests/   --cov=projects/templates/template_literature_meta_analysis/src --cov-fail-under=90 -q
```

The suite uses real fixtures, real files, and `pytest-httpserver`; do not add mocks. See `AGENTS.md` for the test map and `PATTERNS.md` for test idioms.
