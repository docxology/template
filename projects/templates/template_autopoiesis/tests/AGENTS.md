# tests/ — template_autopoiesis

Project test suite (90% coverage floor on `src/`). No mocks — real temp trees
and subprocess CLI invocations.

## Running

```bash
uv run pytest projects/templates/template_autopoiesis/tests/ \
  --cov=projects/templates/template_autopoiesis/src --cov-fail-under=90
```

## Files on disk

This is the complete current test-module inventory (512 collected test
items, including parametrized cases):

| Test module | Collected items |
|---|---:|
| `test_cli.py` | 21 |
| `test_common.py` | 7 |
| `test_cover_art.py` | 29 |
| `test_deps_vendoring.py` | 16 |
| `test_emit_templates.py` | 32 |
| `test_figures.py` | 23 |
| `test_grammar_and_expand.py` | 57 |
| `test_honesty.py` | 17 |
| `test_integrity_and_verify.py` | 32 |
| `test_manuscript_assets_script.py` | 3 |
| `test_manuscript_figures.py` | 9 |
| `test_manuscript_mermaid.py` | 6 |
| `test_manuscript_variables.py` | 14 |
| `test_materialize.py` | 33 |
| `test_meta_teeth.py` | 20 |
| `test_primitives_dynamics.py` | 13 |
| `test_primitives_graph.py` | 17 |
| `test_primitives_optimization.py` | 13 |
| `test_primitives_registry.py` | 10 |
| `test_primitives_signal.py` | 17 |
| `test_primitives_statistics.py` | 13 |
| `test_project_paths.py` | 7 |
| `test_property_invariants.py` | 28 |
| `test_realize.py` | 16 |
| `test_realize_pure.py` | 7 |
| `test_seal_child.py` | 7 |
| `test_sealing.py` | 26 |
| `test_stress_edge_cases.py` | 19 |

The inventory is measured with `pytest --collect-only`; parametrized cases are
counted as separate collected items. `conftest.py` and `__init__.py` are test
support files, not test modules.

## See also

- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)
