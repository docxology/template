# tests/ — template_autopoiesis

Project test suite (90% coverage floor on `src/`). No mocks — real temp trees
and subprocess CLI invocations.

## Running

```bash
uv run pytest projects/templates/template_autopoiesis/tests/ \
  --cov=projects/templates/template_autopoiesis/src --cov-fail-under=90
```

## Files on disk

This is the complete current test-module inventory (528 collected test
items, including parametrized cases). Tests are mirrored one-to-one into
per-cluster directories matching the `src/template_autopoiesis/` subpackage
split (SUBMODULAR-2):

| Test module | Collected items |
|---|---:|
| **`core/`** | |
| `core/test_cli.py` | 21 |
| `core/test_common.py` | 7 |
| `core/test_grammar_and_expand.py` | 67 |
| `core/test_honesty.py` | 17 |
| `core/test_manuscript_mermaid.py` | 6 |
| `core/test_meta_teeth.py` | 20 |
| `core/test_project_paths.py` | 7 |
| `core/test_stress_edge_cases.py` | 19 |
| **`gates/`** | |
| `gates/test_deps_vendoring.py` | 16 |
| `gates/test_integrity_and_verify.py` | 32 |
| `gates/test_materialize.py` | 33 |
| `gates/test_property_invariants.py` | 28 |
| `gates/test_realize.py` | 19 |
| `gates/test_realize_pure.py` | 7 |
| `gates/test_seal_child.py` | 7 |
| `gates/test_sealing.py` | 26 |
| **`figures/`** | |
| `figures/test_cover_art.py` | 29 |
| `figures/test_figures.py` | 23 |
| **`manuscript/`** | |
| `manuscript/test_emit_templates.py` | 32 |
| `manuscript/test_manuscript_assets_script.py` | 3 |
| `manuscript/test_manuscript_contract.py` | 3 |
| `manuscript/test_manuscript_figures.py` | 9 |
| `manuscript/test_manuscript_variables.py` | 14 |
| **`primitives/`** | |
| `primitives/test_primitives_dynamics.py` | 13 |
| `primitives/test_primitives_graph.py` | 17 |
| `primitives/test_primitives_optimization.py` | 13 |
| `primitives/test_primitives_registry.py` | 10 |
| `primitives/test_primitives_signal.py` | 17 |
| `primitives/test_primitives_statistics.py` | 13 |

The inventory is measured with `pytest --collect-only`; parametrized cases are
counted as separate collected items. `conftest.py` and `__init__.py` are test
support files, not test modules.

## See also

- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)
