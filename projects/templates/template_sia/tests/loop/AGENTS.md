# tests/loop/ — agent contract

Behavior tests for `src/template_sia/loop/` (one-to-one mirror per
SUBMODULAR-SIA-1). Domain tests use no mocks. Transport controls may use a
controlled loopback HTTP server, and sandbox controls execute real Docker
containers using an already installed image. They never download dependencies
or call a paid provider. Missing Docker/image preconditions skip those unit
tests; that skip supplies no live acceptance. Actual Ollama acceptance is a
separate explicitly selected model run. Keep test
files co-located with their subject module's subpackage; move a test only
when its subject module moves.

## Files

- `README.md` — scope of this cluster.

## See also

- [`../AGENTS.md`](../AGENTS.md) — shared testing contract.
- [`../../src/template_sia/AGENTS.md`](../../src/template_sia/AGENTS.md) — package-level module map covering `loop/`.
