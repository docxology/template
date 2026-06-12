# Test Notes

No mocks — use real data, fixed RNG seeds, and `tmp_path` for I/O. Each gate and
invariant should have a negative control that proves it fails on bad input.

Gate negative controls live under `tests/gates/` (`test_output_gates.py`,
`test_manuscript_gates.py`, `test_claim_ledger.py`) plus `test_lean_gate.py`.
Use `gate_support.temporary_json_mutation()` for generated-artifact negative
controls so failures restore the mutated JSON byte-for-byte. Small support
helpers remain in `test_support_modules.py`.

Sheaf tests are split by concern: `test_sheaf_manifest.py`, `test_sheaf_registry.py`,
`test_sheaf_compose.py`, `test_sheaf_coverage.py`, `test_sheaf_cli.py`,
`test_coverage_pipeline.py`, `test_sweep_io.py` (no monolithic `test_sheaf.py`).

The gate tests call `compose_all_sections` / `ensure_coverage_artifacts` on the
real project root, which rewrites tracked `manuscript/*.md` (the "Generated
status" table in `08_methods_sheaf.md` and the `00_00_sheaf_coverage.md` page)
to reflect whatever artifacts the run produced. A session-scoped autouse
fixture in `conftest.py` (`_restore_tracked_manuscript`) snapshots every
tracked `manuscript/**/*.md` before the session and restores the byte-for-byte
original at teardown, so the suite always leaves the working tree clean — never
`git commit -a` a degraded status table after a run.

Run full verification from this project root:
`uv run pytest tests/ --cov=src --cov-fail-under=90`. Use focused `-q`
commands only for package-local development loops. Runtime: the full suite is
slow (~15-25 min serial — real pandoc/xelatex and artifact-generation/gate
tests dominate); a quiet console for minutes is expected, not a hang.
