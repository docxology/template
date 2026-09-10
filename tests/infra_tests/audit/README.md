# tests/infra_tests/audit/

Tests for the repo audit scripts under `scripts/audit/` — thin CLI wrappers whose
logic lives in `infrastructure/`. All tests use real files and real subprocesses;
no mocks.

## Run

```bash
uv run pytest tests/infra_tests/audit/ -v
```

## See Also

- [`AGENTS.md`](AGENTS.md)
- [`../../../scripts/audit/README.md`](../../../scripts/audit/README.md)
