# Source Module Notes

Keep all reusable logic in this directory. Scripts under `../scripts/` should
only parse arguments, resolve paths, and call these functions.

## Module map (post quality split)

| Area | Modules | Role |
| --- | --- | --- |
| Loop | `loop.py`, `loop_phases.py`, `writers.py` | Orchestration; phased payload refresh; artifact I/O delegates to sub-writers |
| Writers | `writers_figure_dispatch.py` (re-export), `writers_benchmark.py` | Figure dispatch re-exports from `figure_specs`; benchmark grading |
| Figure specs | `figure_specs.py` | Authoritative labels, methods, dispatch, `build_figure_registry_records` |
| Figure registry metadata | `figure_registry_metadata.py` | Per-label section/width/placement/generated_by/metadata (no filename/id) |
| Figures | `figures.py` (barrel), `figures_ml_*.py`, `figures_process.py`, `figures_security.py`, `figures_core.py` | Matplotlib writers; shared chart primitives in `figures_core` |
| Figure registry | `figure_registry.py` (facade), `figure_registry_{captions,records,contract}.py` | Captions + records derived from specs/static metadata |
| Artifacts | `artifact_loader.py`, `json_coerce.py` | `LoopArtifacts` bundle + shared JSON coercion |
| Manuscript tokens | `manuscript_variables.py` (facade), `manuscript_token_registry.py`, `manuscript_tokens_{core,ml,figures,format}.py` | Render-time `{{TOKEN}}` hydration |
| Manuscript tables | `manuscript_tables.py`, `manuscript_tables_{builders,format}.py` | Registry-backed markdown/PDF tables; `build_table_specs(LoopArtifacts)` |
| Diagnostics | `diagnostics.py` (facade), `diagnostics_{records,intervals,metrics,reports}.py` | ML diagnostic bundles |

Preserve compatibility exports from `ml_task.py`, `figures.py`, `diagnostics.py`,
and `manuscript_variables.py` when moving implementation into split modules.

Add new figure writers under `figures_ml_*` or `figures_process`/`figures_security`;
register keys in `figure_specs.py` (`FIGURE_DISPATCH` + metadata in
`figure_registry_metadata.py`). Filenames and `figure_id` values are derived from
dispatch order at record-build time. Re-export dispatch from `writers_figure_dispatch.py`
when scripts need the legacy import path.

Add manuscript tokens in `manuscript_tokens_ml.py` or `manuscript_tokens_core.py`;
add table builders in `manuscript_tables_builders.py`. Load artifacts once via
`load_loop_artifacts()` before hydrating tokens or tables.
