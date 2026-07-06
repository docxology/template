# Thermo-nuclear code quality review — completed backlog

Maintainability pass over the exemplar's read/write helpers, test ergonomics,
and type-check configuration. No schema, artifact contract, or publication claim
changed; the deterministic toy-only scope is unchanged. This file records
completed cleanup so `TODO.md` stays future-only.

## JSON I/O deduplication

Nine call sites carried their own `_load_json` / `_write_json` copies with
subtly different error handling. They now delegate to the single implementation
in [`../src/json_io.py`](../src/json_io.py):

| Function | Missing file | Malformed JSON |
| --- | --- | --- |
| `load_json` | `{}` | `{}` (lenient) |
| `load_json_strict` | `{}` | raises `ValueError` (fail-closed) |
| `write_json` | creates parents, sorted keys, trailing newline | — |

Modules updated to import from `json_io` (aliases preserved where other modules
import the private names):

- `roadmap_tracks/integration_audit_builders.py` — `load_json` (`_write_json`
  re-exported for `integration_audit.py`).
- `roadmap_tracks/sheaf_tracks_io.py` — re-exports `_load_json` / `_write_json`
  for `sheaf_tracks_write.py` and the sheaf-track builders.
- `roadmap_tracks/supplemental.py`, `roadmap_tracks/visualization_audit.py`,
  `roadmap_tracks/security.py`, `roadmap_tracks/scholarship.py` — lenient
  `load_json` / `write_json`.
- `validation_spine/artifacts.py` and `manuscript/sheaf/semantic_restrictions.py`
  — `load_json_strict`, preserving their fail-closed reads of provenance and
  semantic-gluing artifacts.
- `tests/gate_support.py` — `write_json` in `temporary_json_mutation`.

`formal_interop.py` keeps its local helpers by design; its tests depend on them.

## Test ergonomics

- `pytest-xdist>=3.6.0` added to the `dev` optional-dependency group in
  [`../pyproject.toml`](../pyproject.toml).
- A module-scoped `composed_methods_sheaf` fixture in
  [`../tests/gates/test_manuscript_gates.py`](../tests/gates/test_manuscript_gates.py)
  composes the manuscript once for the methods-sheaf marker negatives instead of
  recomposing per parametrized case. It reads `conftest.PROJECT_ROOT` directly
  because module-scoped fixtures cannot depend on the function-scoped
  `project_root` fixture; the autouse `_restore_mutable_project_state` fixture
  restores the mutated composed section after each test.
- [`../tests/README.md`](../tests/README.md) documents fast-iteration commands:
  `uv sync --extra dev`, `-m "not long_running"`, and isolated `-n auto` for the
  state-free analytical modules (generated-artifact gates stay serial because
  they mutate shared `manuscript/` and `output/` paths).

## Type-check configuration

The root `pyproject.toml` mypy override targeted a path that never existed
(`projects.template_active_inference.*`). It now lists both the real
`projects.templates.template_active_inference.*` namespace and the flat
top-level module names produced by the `src/` layout (`analytical`, `gnn`,
`json_io`, `roadmap_tracks`, `manuscript`, `validation_spine`, …), matching the
`template_literature_meta_analysis` and `template_search_project` pattern. Only
infrastructure is held type-strict.

## Verification

- `ruff check` clean across every touched module.
- Import smoke test confirms all re-exported `_load_json` / `_write_json`
  aliases resolve and the full `roadmap_tracks` package imports.
- `pytest tests/gates/test_manuscript_gates.py -k methods_sheaf_layers_negative`
  — 5 passed via the shared fixture.
- Full-suite coverage evidence and reproduction commands remain in
  [`../TODO.md`](../TODO.md) and [`../tests/README.md`](../tests/README.md).
