# Testing Philosophy: The Zero-Mock Standard

This methods-DSL exemplar strictly forbids mocking in gate, compiler, and
exporter validation.

## Why Zero Mocks?

The core insight is architectural: if a function requires a mock to be
tested, it is doing I/O, plotting, or producing side-effects — which means it
belongs in `scripts/` (a thin orchestrator), not in `src/methods_dsl/` (pure
model/validation/compilation logic). The purity of `src/methods_dsl/` is what
makes zero-mock testing achievable. Every function takes real dataclasses
(`Method`, `Step`, `Quantity`, ...) in and returns real data out, so tests
simply construct a real `Method` and verify real gate outcomes, plan hashes,
or exported text.

If you ever feel the urge to mock something in a test for `src/`, treat it as
a signal: move that code to `scripts/` and test the `src/` boundary directly.

## The Validation Suite

| File | Role |
| --- | --- |
| `test_vocabulary.py` | `StepKind`, `Target`, `target_accepts` compatibility table |
| `test_units.py` | `dimension_of`, `Quantity` arithmetic, `DimensionError` on mismatch, `known_units` |
| `test_model.py` | `Method`/`Step`/`Resource`/`Parameter` shape validation (`__post_init__` errors) |
| `test_validation.py` | Each of the four staged gates, `run_all_gates` ordering and short-circuit |
| `test_compiler.py` | `topological_order` (linear + diamond DAGs, cycle detection), `compile_method` determinism |
| `test_export.py` | Worklist markdown, CSV, Mermaid, and canonical-JSON renderers |
| `test_trust.py` | `ProvenanceTier`, hash-chain append/verify, tamper detection |
| `test_examples_methods.py` | The two worked example methods pass every gate and compile |
| `test_project_paths.py` | `project_output_dirs` and `resolve_project_root` path plumbing |
| `test_manuscript_variables.py` | Every `{{TOKEN}}` referenced in `manuscript/*.md` is emitted |
| `test_methods_analysis_script.py` | Thin script `run_methods_analysis()` writes real exports + reports + a figure to a temp root |

Configuration: `projects/templates/template_methods_paper/pyproject.toml`
(`fail_under = 90`, matching the root pipeline gate).

Conftest: `projects/templates/template_methods_paper/tests/conftest.py`
(sets `MPLBACKEND=Agg`, adds `src/` and the repo root to `sys.path`, and
ships shared `Method` fixtures — `linear_method`, `diamond_method`, and one
fixture per gate-failure mode).

Live test count and coverage percentage:
[`docs/_generated/COUNTS.md`](../../../../docs/_generated/COUNTS.md)
(or `uv run pytest tests/ --collect-only -q` from the project directory).

## Test Organization

This suite uses **flat function-style tests** (`def test_<what_is_being_tested>`),
not class-based tests — there is no `class Test...` declared anywhere under
`tests/`. Each `test_<module>.py` file mirrors `src/methods_dsl/<module>.py`
one-to-one. See [`../tests/AGENTS.md`](../tests/AGENTS.md) before introducing
a class-based test, since the `test_class_drift` drift gate fails if any doc
names a test class absent from `tests/`.

## Coverage Mechanics

```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = ["tests/*", "*/__init__.py", "*/test_*.py"]

[tool.coverage.report]
fail_under = 90
```

Authoritative gate (measures all of `src/`):

```bash
cd projects/templates/template_methods_paper
uv run pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=90
```

## Zero-Mock Checklist

- [ ] Test constructs a real `Method`/`Step`/`Resource`/`Quantity` (or reuses
      a `conftest.py` fixture) as input.
- [ ] Test calls `src/methods_dsl/` functions directly with that real input.
- [ ] Test asserts real outcomes (gate `passed`/`issues`, a recomputed
      `plan_hash`, exported text content), not call counts.
- [ ] No `unittest.mock`, `MagicMock`, `create_autospec`, `@patch`, or mock
      factories anywhere.
- [ ] Determinism tests compile the same `Method` object twice and compare
      hashes live, never against a hardcoded hash literal.

## Structural Rule: If You Need a Mock, Move the Code

- **`src/methods_dsl/*`** — pure model/validation/compilation/export/trust
  logic; no plotting, no file I/O, no `infrastructure.*` imports except the
  one declared exception in `_logging.py`.
- **`scripts/methods_analysis.py`** — the only place matplotlib and file
  writes live; tested by `test_methods_analysis_script.py` against a temp
  root.

## Running the Gate

A green exit code is **not** proof the suite ran. Confirm **N collected > 0
AND coverage ≥ 90%**.

```bash
cd projects/templates/template_methods_paper
uv run pytest tests/ --cov=src --cov-fail-under=90 -q
```

See [`troubleshooting.md`](troubleshooting.md).
