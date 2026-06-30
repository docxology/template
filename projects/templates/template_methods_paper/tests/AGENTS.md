# `template_methods_paper/tests/` - agent guide

## Purpose

Exercises every public function in `src.methods_dsl` (and the thin
`scripts/methods_analysis.py` orchestrator) against real `Method` objects —
never mocks. Coverage gate: ≥90% on `src/` (`pyproject.toml`
`[tool.coverage.report] fail_under = 90`).

## Rules

- No `unittest.mock`, no `MagicMock`, no stubbed return objects — every test
  constructs a real `Method`/`Step`/`Resource`/`Quantity` and calls the real
  function (zero-mock policy, repo-wide).
- One test function per behavior (`def test_<what_is_being_tested>`); this
  suite uses flat function-style tests, not class-based tests — there is no
  `class Test...` anywhere under `tests/`, so do not introduce one without
  also updating this file (the `test_class_drift` drift rule fails on any
  doc that names a class absent from `tests/`).
- Reuse the shared fixtures in `conftest.py` (`linear_method`,
  `diamond_method`, and one fixture per gate-failure mode) instead of
  hand-rolling a near-duplicate `Method` inline.
- Every `Raises:` clause documented in `src/methods_dsl/*.py` has a
  corresponding `pytest.raises(..., match=...)` test.
- Determinism claims (`compile_method` plan-hash stability) are tested by
  compiling the *same* method object twice and asserting the hashes are
  equal — not by asserting against a hardcoded hash literal, which would
  silently stop testing the moment the compiler's hash input changed.

## See Also

- [`README.md`](README.md) - file-by-file coverage map
- [`PATTERNS.md`](PATTERNS.md) - fixture and assertion patterns
- [`../src/AGENTS.md`](../src/AGENTS.md) - the library under test
