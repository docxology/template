# Source Module Notes

Keep all reusable logic in this directory. Scripts under `../scripts/` should
only parse arguments, resolve paths, and call these functions.

## Module map (post quality split)

| Area | Modules | Role |
| --- | --- | --- |
| Loop | `loop.py`, `loop_phases.py`, `writers/` | Orchestration; phased payload refresh; artifact I/O delegates to `writers/` submodules |
| Writers | `writers/figure_dispatch.py`, `writers/benchmark.py`, `writers/{io,manifests,payloads}.py` | Figure dispatch from `figures.figure_specs`; benchmark grading; JSON/CSV/manifest I/O (`writers/__init__.py` facade) |
| Figure specs | `figures/figure_specs.py` | Authoritative labels, methods, dispatch, `build_figure_registry_records` |
| Figure registry metadata | `figures/figure_registry_metadata.py` | Per-label section/width/placement/generated_by/metadata (no filename/id) |
| Figures | `figures/figures_ml_*.py`, `figures/figures_process.py`, `figures/figures_security.py`, `figures/figures_core.py` | Matplotlib writers; shared chart primitives in `figures_core` (`figures/__init__.py` barrel) |
| Figure registry | `figures/figure_registry.py` (facade), `figures/figure_registry_{captions,records,contract}.py` | Captions + records derived from specs/static metadata |
| Artifacts | `artifact_loader.py`, `json_coerce.py` | `LoopArtifacts` bundle + shared JSON coercion |
| Manuscript tokens | `manuscript_variables.py` (root facade), `manuscript/manuscript_token_registry.py`, `manuscript/manuscript_tokens_{core,ml,figures,format}.py` | Render-time `{{TOKEN}}` hydration |
| Manuscript tables | `manuscript/manuscript_tables.py`, `manuscript/manuscript_tables_{builders,format}.py` | Registry-backed markdown/PDF tables; `build_table_specs(LoopArtifacts)` |
| Diagnostics | `diagnostics/{records,intervals,metrics,reports}.py` (`diagnostics/__init__.py` facade) | ML diagnostic bundles |
| Source ledger | `source_ledger.py` | Offline (no-network) validation of `manuscript/source_ledger.yaml` against `references.bib` and manuscript citations; source-tier counts and checked-age buckets for reviewer reports |

Each package's `__init__.py` is the public facade — re-export new public symbols
there rather than recreating flat root-level stub modules (the flat→package
migration is complete; no `ml_task.py`/`figures.py`/`diagnostics.py` root stubs exist).

Add new figure writers under `figures/figures_ml_*` or `figures/figures_process`/`figures/figures_security`;
register keys in `figures/figure_specs.py` (`FIGURE_DISPATCH` + metadata in
`figures/figure_registry_metadata.py`). Filenames and `figure_id` values are derived from
dispatch order at record-build time. Figure dispatch lives in `writers/figure_dispatch.py`
and re-exports from `figures.figure_specs`.

Add manuscript tokens in `manuscript/manuscript_tokens_ml.py` or `manuscript/manuscript_tokens_core.py`;
add table builders in `manuscript/manuscript_tables_builders.py`. Load artifacts once via
`load_loop_artifacts()` before hydrating tokens or tables.
