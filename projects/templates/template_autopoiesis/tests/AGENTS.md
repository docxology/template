# tests/ — template_autopoiesis

Project test suite (90% coverage floor on `src/`). No mocks — real temp trees
and subprocess CLI invocations.

## Running

```bash
uv run pytest projects/templates/template_autopoiesis/tests/ \
  --cov=projects/templates/template_autopoiesis/src --cov-fail-under=90
```

## Files on disk

The current test modules are mirrored into directories matching their source
clusters. Measure collected cases with `pytest --collect-only`; current repository
measurements belong in `docs/_generated/COUNTS.md`.

- `core/test_cli.py`
- `core/test_common.py`
- `core/test_grammar_and_expand.py`
- `core/test_honesty.py`
- `core/test_manuscript_mermaid.py`
- `core/test_meta_teeth.py`
- `core/test_project_paths.py`
- `core/test_stress_edge_cases.py`
- `figures/test_cover_art.py`
- `figures/test_figures.py`
- `gates/test_deps_vendoring.py`
- `gates/test_integrity_and_verify.py`
- `gates/test_materialize.py`
- `gates/test_property_invariants.py`
- `gates/test_realization_contract.py`
- `gates/test_realize.py`
- `gates/test_realize_pure.py`
- `gates/test_seal_child.py`
- `gates/test_sealing.py`
- `manuscript/test_emit_templates.py`
- `manuscript/test_manuscript_assets_script.py`
- `manuscript/test_manuscript_contract.py`
- `manuscript/test_manuscript_figures.py`
- `manuscript/test_manuscript_variables.py`
- `primitives/test_primitives_dynamics.py`
- `primitives/test_primitives_graph.py`
- `primitives/test_primitives_optimization.py`
- `primitives/test_primitives_registry.py`
- `primitives/test_primitives_signal.py`
- `primitives/test_primitives_statistics.py`

## See also

- [`../AGENTS.md`](../AGENTS.md)
- [`README.md`](README.md)


Standalone provider contract: prepare the project's own dependencies and the genuine platform SDK pinned in its package metadata and lock, then invoke own scripts or `python -I -m pytest tests/ --cov=src --cov-fail-under=90`. `_bootstrap.py` selects the environment SDK before registering the exact own package namespace; it adds no own src or inferred parent root to global import paths. A genuinely missing SDK remains absent and the selected-child execution producer records blocked/75 before materialization. Root-checkout metadata poison controls belong to Root tests; they do not manufacture checkout files in wheel site-packages. Installed execution and complete-source reference data remain independently bound acceptance lanes.
