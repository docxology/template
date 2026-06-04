# Manuscript package

| Module | Role |
| --- | --- |
| `__init__.py` | `compute_variables`, `write_manuscript_hydration_artifacts` |
| `manuscript_token_registry.py` | Token registry |
| `manuscript_tokens_*.py` | Core, ML, figure, format tokens |
| `manuscript_tables_builders.py`, `manuscript_tables_format.py` | Table specs and formatting |

Load artifacts once via `load_loop_artifacts()` before hydrating tokens or tables.
