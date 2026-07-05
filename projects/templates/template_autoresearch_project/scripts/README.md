# Scripts

Thin orchestrators for the AutoResearch exemplar. Each script imports
[`_bootstrap.py`](_bootstrap.py) for shared `sys.path` setup.

- `run_autoresearch_loop.py` calls `src.loop.run_autoresearch_loop()`.
- `z_generate_manuscript_variables.py` calls `src.manuscript_variables` and
  `infrastructure.rendering.manuscript_injection`.
- `check_source_ledger.py` validates `manuscript/source_ledger.yaml` offline and
  prints tier and checked-age counts.
- `regenerate_mnist_fixture.py` regenerates `data/mnist_small.npz` and provenance;
  manual maintenance only (not invoked by the default pipeline).
