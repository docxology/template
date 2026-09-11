# tests/loop/ — agent contract

Behavior tests for `src/template_sia/loop/` (one-to-one mirror per
SUBMODULAR-SIA-1). Pure-domain tests only: no mocks, no network;
subprocess invocations target this project's own entrypoints. Keep test
files co-located with their subject module's subpackage; move a test only
when its subject module moves.

## Files

- `README.md` — scope of this cluster.

## See also

- [`../AGENTS.md`](../AGENTS.md) — shared testing contract.
- [`../../src/template_sia/AGENTS.md`](../../src/template_sia/AGENTS.md) — package-level module map covering `loop/`.
