# Health-gate fixture agent guide

- Preserve this dependency-free virtual project and its standalone workspace.
- Keep `pyproject.toml` and the genuinely generated `uv.lock` consistent.
- Do not unset `UV_FROZEN`, generate locks during tests, add dependency
  replacements, or weaken stage-table success and failure controls.
- Verify changes through the existing real stage-table health-registry cases in
  [`test_health.py`](../../infra_tests/core/test_health.py).
- These files are test inputs, not SDK runtime or publication evidence.

See [fixture purpose](README.md) and [parent guidance](../AGENTS.md).
