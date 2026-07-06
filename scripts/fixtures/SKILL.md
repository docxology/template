---
name: template-fixtures
description: |
  Fixture download scripts for test data. Downloads real GitHub repos
  (requests, fastapi) via sparse checkout and M4 monthly timeseries data
  from Hugging Face with synthetic fallback. Resumable — skips if target
  directory already exists and is non-empty.
---
# SKILL: template-fixtures

Test fixture download scripts.

## Invocation

```bash
uv run python scripts/fixtures/download_real_codebases.py
uv run python scripts/fixtures/download_timeseries_benchmarks.py
```

## Related

- `scripts/fixtures/AGENTS.md` — detailed documentation
- `tests/fixtures/` — fixture storage directory