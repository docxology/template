# tests/pipeline/ — agent contract

Behavior tests for `src/template_prose_project/pipeline/` (one-to-one mirror
per SUBMODULAR-PROSE-1). Pure-domain tests only: no mocks, no network;
subprocess invocations target this project's own entrypoints. Keep test
files co-located with their subject module's subpackage; move a test only
when its subject module moves.

## Files

- `README.md` — scope of this cluster.
- `pipeline_helpers.py` — shared helper: calls `infrastructure.prose.analyze_manuscript`
  before `src.pipeline.run_prose_pipeline`; imported flat by the integration tests
  in this directory.

## See Also

- [`../AGENTS.md`](../AGENTS.md) — shared testing contract.
- [`../../src/template_prose_project/AGENTS.md`](../../src/template_prose_project/AGENTS.md) — package-level module map covering `pipeline/`.
