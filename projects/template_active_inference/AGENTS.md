# AGENTS.md — template_active_inference

Multi-track Active Inference public exemplar. Manuscript sections follow an **IMRAD outline** composed from sheaf fragment tracks (prose, formalism, simulation, pymdp, visualization, Lean, GNN, ontology, animation).

## Sheaf composition (registry-driven)

| File | Role |
| --- | --- |
| [`manuscript/sheaf/tracks.yaml`](manuscript/sheaf/tracks.yaml) | Fragment registry — order, renderer, optional flag |
| [`manuscript/sheaf/manifest.yaml`](manuscript/sheaf/manifest.yaml) | IMRAD matrix (`{{imrad_manifest_rows}}` rows at compose time) |
| [`manuscript/sheaf/coverage.yaml`](manuscript/sheaf/coverage.yaml) | Coverage report + heatmap styling |
| [`figures.yaml`](figures.yaml) | Figure style, alt text, captions, `section_figures` map |
| [`src/manuscript/sheaf/`](src/manuscript/sheaf/) | Registry, manifest, compose, coverage, report |
| [`tracks.yaml`](tracks.yaml) | Pipeline gates (`{{pipeline_track_count}}` required tracks) |

**Compose + coverage:**

```bash
uv run python scripts/compose_manuscript.py
uv run python scripts/compose_manuscript.py --validate-only --strict
uv run python scripts/compose_manuscript.py --section methods_pymdp --tracks prose,pymdp
uv run python scripts/z_generate_manuscript_variables.py
```

Full compose calls `emit_coverage_artifacts()` → JSON, heatmap PNG, and regenerated [`manuscript/00_00_sheaf_coverage.md`](manuscript/00_00_sheaf_coverage.md) with registry-backed heatmap alt/caption. Coverage PNG/page emission is built into `compose_all_sections()` (script is a thin CLI wrapper).

**Visualization track:** renderer `section_figures` in [`tracks.yaml`](manuscript/sheaf/tracks.yaml); `resolve_track_body()` calls `render_section_figures()` (fragment `.md` files are stubs).

**Generated renderers:** `section_figures` (figures from `figures.yaml`) and `layers_report` (registry + binding matrix tables). Dispatch is centralized in [`renderers.resolve_track_body()`](src/manuscript/sheaf/renderers.py) — no section-specific branches in `compose.py`.

**Manuscript variables** (`src/manuscript/variables.py`, `src/manuscript/hydrate.py`):

| Token | Source |
| --- | --- |
| `pipeline_track_count` | `tracks.yaml` required tracks |
| `sheaf_track_count` | `manuscript/sheaf/tracks.yaml` |
| `appendix_sheaf_track_count` | tracks bound in `appendix_full_sheaf` manifest section |
| `imrad_manifest_rows`, `composed_section_count`, `imrad_group_count` | live manifest |
| `coverage_present`, `coverage_bound`, `coverage_missing` | coverage matrix at variable generation |
| `invariants_passed`, `invariants_total` | merged `output/reports/invariants.json` when present (analytical + simulation); else live analytical run |
| `si_tmaze_policy_len`, … | measured analysis artifacts |
| `ising_mi_saturation` | max closed-form MI on `parameter_sweep.csv` (grid maximum, nats) |
| `si_goal_reached`, `si_action_diversity`, `si_entropy_min/max` | `analysis_statistics.json` / SI summary |
| `sweep_max_residual`, `sweep_rmse_mi` | analytical sweep statistics |
| `pymdp_mode`, `pymdp_config_hash` | `pymdp.yaml` + SI summary |

`z_generate_manuscript_variables.py` writes `output/data/manuscript_variables.json` and resolves `output/manuscript/` for PDF rendering. Compose emits `{{token}}` placeholders; hydration is the single substitution boundary (fail-closed on unknown or single-brace `{token}` typos).

## pymdp configuration

| File | Role |
| --- | --- |
| [`pymdp.yaml`](pymdp.yaml) | Horizon, steps, seed, mode, T-maze likelihood/preference, agent flags, logging path |
| [`src/simulation/pymdp_config.py`](src/simulation/pymdp_config.py) | `load_pymdp_config()`, `apply_pymdp_overrides()`, `config_hash()` |
| [`src/simulation/si_runner.py`](src/simulation/si_runner.py) | Facade → `si_{belief,policy,loop,artifacts}.py`; `run_si_tmaze()`, `run_and_persist()` |
| [`src/simulation/invariants.py`](src/simulation/invariants.py) | Simulation-track invariants merged into `output/reports/invariants.json` |
| [`src/simulation/statistics.py`](src/simulation/statistics.py) | `summarize_si_trace()` for `analysis_statistics.json` |

```bash
uv run python scripts/simulate_si_tmaze.py --help
uv run python scripts/simulate_si_tmaze.py --seed 0 --mode state_inference
uv run python scripts/compute_statistics.py
```

JSONL logging: `output/logs/pymdp_runs.jsonl` (`si_tmaze_run_header` + `si_tmaze_step` events). Run report: `output/reports/si_tmaze_run_report.json`.

**SI figures** (`figures.yaml`): `si_belief_entropy_curve`, `si_obs_action_trace`, `si_tmaze_actions` bound under `results_si_tmaze` (Figure 3a–3c). **Sheaf layers figure:** `sheaf_layers_overview` (two-panel registry stack + heatmap) bound under `methods_sheaf` as Figure 6 (methods). **Appendix:** Figure A1/A2 for MI/actions; Figure 4 for coverage heatmap. **Front matter:** coverage page uses “Coverage overview.” caption without a figure number.

**Discussion sheaf tracks:** `discussion_outlook` binds `prose`, `simulation`, and `ontology` fragments with measured tokens.

**Methods sheaf layers (main body):** `methods_sheaf` uses explicit `track_order: [prose, formalism, visualization, layers]`. Layers overview figure via `visualization` / `section_figures`; tables via optional `layers` track / `layers_report` renderer with HTML markers `sheaf-layers:*`. Front-matter audit page [`manuscript/00_00_sheaf_coverage.md`](manuscript/00_00_sheaf_coverage.md) uses `section_figures.coverage_page` (no duplicate figure number vs appendix Figure 4).

**Package modules** (`src/manuscript/sheaf/`):

| Module | Role |
| --- | --- |
| `models.py` | `SheafSection`, `CoverageMatrix`, IMRAD types |
| `manifest.py` | Load `manifest.yaml` |
| `compose.py` | `compose_all_sections`, `validate_manifest` |
| `coverage.py` | `emit_coverage_artifacts`, JSON export |
| `report.py` | `write_coverage_page`, `render_report_markdown` |
| `layers_report.py` | `render_sheaf_layers_markdown`, table renderers, `sheaf-layers:*` markers |
| `counts.py` | `structural_counts()` for registry-backed manuscript tokens |
| `renderers.py` | `RENDERERS`, `resolve_track_body`, generated renderer dispatch |

**Visualizations** (`src/visualizations/`): `figure_style.py`, `figure_registry.py`, `figure_io.py`, `figures.py` (`run_figure`, unified RGB save), `figures_sheaf.py` (facade → `figures_sheaf_{payload,draw}.py`). `FIGURE_GENERATORS` in `figures.py` mirrors `figures.yaml` ids; free-energy plots use `lambda_grid()` SSOT.

**Appendix proof:** `appendix_full_sheaf` binds nine registry tracks (all except optional `layers`) → `16_appendix_full_sheaf.md`. Registry defines ten fragment types total.

Edit fragments only under [`manuscript/sections/imrad/`](manuscript/sections/imrad/). Manual closing section: [`manuscript/17_conclusion.md`](manuscript/17_conclusion.md) (outside the matrix).

## Layout

| Path | Role |
| --- | --- |
| `src/orchestration/` | `analysis.py` (analysis entry), `coverage_pipeline.py` (coverage PNG + page after compose) |
| `src/analytical/` | Bernoulli K=2 closed form; `invariants.py` — analytical invariant registry |
| `src/invariants.py` | Thin re-export facade → `analytical/invariants.py` |
| `src/simulation/` | pymdp T-maze SI harness (`si_runner.py` facade + `si_*.py` modules) + JSONL logging |
| `src/gnn/` | GNN parser + ontology concordance |
| `src/ontology/` | Section ontology YAML helpers (`load_section_ontology` flattens nested `terms:` blocks) |
| `src/gates/` | `validation.py` facade; `output_checks`, `manuscript_checks`, `claim_ledger`, `lean` |
| `gnn/*.gnn.md` | GNN source files |
| `lean/TemplateActiveInference/` | Lean witnesses — `build_lean` gate runs `lake build` when `lean/lakefile.lean` exists; absent Lean tree skips cleanly |
| `scripts/` | Thin orchestrators only |

## Commands

```bash
uv run python scripts/compose_manuscript.py
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run python scripts/validate_outputs.py
```

## Parent docs

- Root [`AGENTS.md`](../../AGENTS.md)
- [`tracks.yaml`](tracks.yaml)
