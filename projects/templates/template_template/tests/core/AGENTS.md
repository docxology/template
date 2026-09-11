# tests/core/ — agent contract

Behavior tests for `src/template_template/core/` (one-to-one mirror).
Pure-domain tests only: no mocks, no network; subprocess invocations target
this project's own entrypoints. Keep test files co-located with their subject
module's subpackage; move a test only when its subject module moves.

## Files

- `test_meta.py` — introspection, injection, and real-manuscript integration
- `test_contracts.py` — receipt schema, matrix lockstep, deterministic defaults
- `test_confidentiality.py` — public/private discovery boundary (negative controls)
- `test_edge_cases.py` — error branches, fallbacks, previously-uncovered paths
- `test_script_entrypoints.py` — sandboxed subprocess execution of the metrics orchestrator

## See Also

- [`../AGENTS.md`](../AGENTS.md) — shared testing contract.
- [`../../src/template_template/AGENTS.md`](../../src/template_template/AGENTS.md) — package-level module map covering `core/`.
