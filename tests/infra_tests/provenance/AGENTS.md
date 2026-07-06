# tests/infra_tests/provenance/ — Provenance module tests

Tests for `infrastructure.provenance` store, review, and opt-in stage
`scripts/pipeline/stage_09_provenance_record.py`.

## Files

- `test_store.py` — provenance store read/write
- `test_review.py` — review helpers
- `test_provenance_scripts.py` — stage script CLI surface

## Running

```bash
uv run pytest tests/infra_tests/provenance/ -v
```

## See also

- [`../../../infrastructure/provenance/`](../../../infrastructure/provenance/)
- [`README.md`](README.md)
