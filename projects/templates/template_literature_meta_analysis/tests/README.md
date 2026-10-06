# Tests - Literature Meta-Analysis

From the template monorepo root, run the isolated project gate:

```bash
uv run python scripts/pipeline/stage_01_test.py --project templates/template_literature_meta_analysis --project-only
```

From an independent exemplar checkout's root, prepare its own platform/dev
environment following [`../STANDALONE.md`](../STANDALONE.md), then run its
configured coverage gate:

```bash
python -I -m pytest tests/ --cov=src --cov-fail-under=90
```

The suite uses real fixtures, real files, and `pytest-httpserver`; do not add mocks. See `AGENTS.md` for the test map and `PATTERNS.md` for test idioms.
