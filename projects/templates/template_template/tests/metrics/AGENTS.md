# tests/metrics/ — agent contract

Behavior tests for `src/template_template/metrics/` (one-to-one mirror).
Pure-domain tests only: no mocks, no network; subprocess invocations target
this project's own entrypoints. Keep test files co-located with their subject
module's subpackage; move a test only when its subject module moves.

## Files

- `test_metrics.py` — metric helpers and live-repository integration
- `test_evidence_contract.py` — executable policy binding + evidence fail-closed controls
- `test_stale_metrics_control.py` — stale-metric negative controls

## See Also

- [`../AGENTS.md`](../AGENTS.md) — shared testing contract.
- [`../../src/template_template/AGENTS.md`](../../src/template_template/AGENTS.md) — package-level module map covering `metrics/`.
