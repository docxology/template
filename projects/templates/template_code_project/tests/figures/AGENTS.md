# tests/figures/ — agent contract

Behavior tests for `src/template_code_project/figures/` (one-to-one
mirror per SUBMODULAR-CODE-2). Pure-domain tests only: no mocks, no
network; subprocess invocations target this project's own entrypoints.
Keep test files co-located with their subject module's subpackage; move a
test only when its subject module moves, via `git mv`.

## Files

- `README.md` — scope of this cluster.

## See Also

- [`../AGENTS.md`](../AGENTS.md) — shared testing contract.
- [`../../src/template_code_project/AGENTS.md`](../../src/template_code_project/AGENTS.md) — package-level module map covering `figures/`.
