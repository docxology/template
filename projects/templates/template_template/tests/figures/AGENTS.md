# tests/figures/ — agent contract

Behavior tests for `src/template_template/figures/` (one-to-one mirror).
Pure-domain tests only: no mocks, no network; matplotlib runs headless via
conftest (`MPLBACKEND=Agg`). Keep test files co-located with their subject
module's subpackage; move a test only when its subject module moves.

## Files

- `test_architecture_viz.py` — comparative-matrix invariants and real PNG generation

## See Also

- [`../AGENTS.md`](../AGENTS.md) — shared testing contract.
- [`../../src/template_template/AGENTS.md`](../../src/template_template/AGENTS.md) — package-level module map covering `figures/`.
