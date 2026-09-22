# `template_experiment_tree/tests/`

Agent guide for the test suite. Run instructions and the coverage floor
are documented in [`../README.md`](../README.md#configuration-and-validation).

## Layout

| File | Tests |
|---|---|
| `test_tree.py` | Tree-model contract: status ladder, frozen-node refusal, conflicting `run_command`, unknown parent / duplicate ids, outcome validation. |
| `test_store.py` | Store round-trip against real `tmp_path` files; deterministic output; wrong-schema and malformed-node negative controls. |
| `test_report.py` | `summarize` counts, `render_markdown` sections (including empty-tree), `render_variables`, `flatten_sections`, fail-closed `resolve_token_map`. |
| `test_manuscript_variables.py` | `generate_variables` JSON output, `require_answered` fail-closed, missing store, `resolve_tokens` negative control. |
| `test_scripts_smoke.py` | Real `subprocess.run` against every script in `scripts/` (init, record, report, hydration). |
| `conftest.py` | Puts `src/` on `sys.path` for pytest imports. |

## Conventions

- **No mocks.** Real trees, real JSON files, real subprocess calls.
- **`tmp_path` for isolation.** Tests never mutate the project's own
  `output/data/experiment_tree.json`; script smoke tests copy the store
  to a temp path before recording.
- **Negative controls lock the invariants.** Each invariant in
  [`../AGENTS.md`](../AGENTS.md#invariants-each-locked-by-a-negative-control-test)
  has a test asserting the raise: answering a frozen node, conflicting
  run_command, unbacked manuscript token.
- **Fail-closed over silent defaults.** New behavior that could silently
  mask a broken tree or missing token deserves a `pytest.raises` test.

## Editing rules

- **Tests mirror src.** A new public function in `src/template_experiment_tree/<x>.py` gets coverage in `tests/test_<x>.py`.
- **New invariant → new negative control.** A new `ExperimentTree` refusal gets its `pytest.raises` case in `test_tree.py` in the same change.
- **Script behavior changes belong in `test_scripts_smoke.py`** — real exit codes and stdout markers (`REFUSED`, `FAILED`, `already exists`).

## See also

- [`../AGENTS.md`](../AGENTS.md) — invariants and ground truth.
- [`../scripts/AGENTS.md`](../scripts/AGENTS.md) — the orchestrators the
  smoke tests exercise.