# Doctor detectors package

## Public API

- `DETECTORS: tuple[DetectorFn, ...]` — canonical registration order (`registry.py`)
- `run_detectors(repo_root, selected=None) -> list[Finding]` — crash-isolated runner
- Individual `detect_*` functions re-exported for tests and CLI wiring

## Invariants

- Detectors are idempotent and side-effect free (read-only probes only).
- A detector exception becomes a CRITICAL `DOC000[fn]` finding; never aborts the run.

## Tests

```bash
uv run pytest tests/infra_tests/doctor/test_detectors.py -q
```
