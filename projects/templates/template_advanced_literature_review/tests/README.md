# Tests

The project suite covers configuration, phase filtering and provenance,
cross-phase deduplication, deep-research replay, full-text handling, manuscript
variables, and the standalone pipeline contract.

Run the canonical gate from the repository root:

```bash
uv run python scripts/pipeline/stage_01_test.py \
  --project templates/template_advanced_literature_review --project-only
```

Tests use real parsers, temporary files, and local HTTP servers. They must not
use prohibited mock frameworks or replace semantic dependencies.
