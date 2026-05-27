# Test Notes

No mocks — use real data, fixed RNG seeds, and `tmp_path` for I/O. Each gate and
invariant should have a negative control that proves it fails on bad input.

Gate negative controls live in `test_support_modules.py` (`methods_sheaf_layers`,
`full_sheaf_appendix_tracks`, `gnn_concordance`, `claim_ledger_valid`,
`manuscript_tokens_registered`, `resolved_manuscript_hydrated`, `validate_outputs`,
`build_lean`).

Sheaf tests are split by concern: `test_sheaf_manifest.py`, `test_sheaf_registry.py`,
`test_sheaf_compose.py`, `test_sheaf_coverage.py`, `test_sheaf_cli.py` (no monolithic
`test_sheaf.py`).

Run: `uv run pytest projects/template_active_inference/tests -q`.
