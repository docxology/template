# Scripts - Agent Notes

Keep scripts thin. Do not add reusable logic here; add it to `../src/` and call
it from the script.

Shared `sys.path` setup lives in [`_bootstrap.py`](_bootstrap.py) (`ensure_project_paths`).

| Script | Delegates to |
| --- | --- |
| `run_autoresearch_loop.py` | `src.loop.run_autoresearch_loop` |
| `z_generate_manuscript_variables.py` | `src.manuscript_variables`, `infrastructure.rendering.manuscript_injection` |
| `check_source_ledger.py` | `src.source_ledger` validators |
| `regenerate_mnist_fixture.py` | `src.ml.mnist_fixture.regenerate_mnist_fixture` (maintenance only) |
