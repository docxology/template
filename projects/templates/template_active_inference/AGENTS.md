# AGENTS.md — template_active_inference

Multi-track Active Inference public exemplar. Manuscript sections follow an **IMRAD outline** composed from stable canonical sheaf fragment tracks (prose, formalism, simulation, assumption index, pymdp, interop, provenance, replay matrix, counterexample, adversarial audit, evidence fields, release bundle, gate ergonomics, sensitivity, uncertainty, benchmark, manuscript staleness, visualization, Lean, model checking, theorem traceability, GNN, ontology, animation, animation delta).

## Sheaf composition (registry-driven)

| File | Role |
| --- | --- |
| [`manuscript/sheaf/tracks.yaml`](manuscript/sheaf/tracks.yaml) | Fragment registry — order, renderer, optional flag |
| [`manuscript/sheaf/manifest.yaml`](manuscript/sheaf/manifest.yaml) | IMRAD matrix; row counts come from generated manuscript variables |
| [`manuscript/sheaf/coverage.yaml`](manuscript/sheaf/coverage.yaml) | Coverage report + heatmap styling |
| [`figures.yaml`](figures.yaml) | Figure style, alt text, captions, `section_figures` map |
| [`src/manuscript/sheaf/`](src/manuscript/sheaf/) | Registry, manifest, compose, coverage, report |
| [`tracks.yaml`](tracks.yaml) | Pipeline gates; required-track count comes from generated manuscript variables |

**Compose + coverage:**

```bash
uv run python scripts/compose_manuscript.py
uv run python scripts/compose_manuscript.py --validate-only --strict
uv run python scripts/compose_manuscript.py --section methods_pymdp --tracks prose,pymdp
uv run python scripts/z_generate_manuscript_variables.py
```

Full compose calls `emit_coverage_artifacts()` → JSON only. `generate_figures.py` calls `ensure_coverage_artifacts()` for heatmap PNG + regenerated [`manuscript/00_00_sheaf_coverage.md`](manuscript/00_00_sheaf_coverage.md). Coverage PNG/page emission is no longer part of `compose_all_sections()` (script is a thin CLI wrapper).

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
| `validation_spine_artifact_count`, `replay_matrix_row_count`, `counterexample_count` | promoted validation-spine and canonical replay artifacts |
| `pymdp_runtime_known_warning_count`, `pymdp_runtime_unexpected_warning_count`, `pymdp_policy_posterior_row_count` | scoped pymdp/JAX runtime diagnostics + posterior grid |
| `sensitivity_cell_count`, `uncertainty_row_count`, `benchmark_model_count`, `analytical_assumption_count`, `si_graph_world_topology_trace_count` | promoted toy sweep artifacts |
| `model_checking_witness_count`, `interop_check_count`, `adversarial_audit_count` | formal interop and audit artifacts |
| `semantic_restriction_count`, `dependency_edge_type_count`, `stale_artifact_fresh_count`, `manuscript_staleness_row_count`, `figure_source_coverage_count`, `scope_boundary_status` | semantic and integration audit artifacts |
| `provenance_bundle_count`, `evidence_field_count`, `release_bundle_artifact_count`, `theorem_traceability_row_count`, `validation_gate_index_count`, `track_improvement_row_count` | canonical sheaf-track artifacts |
| `artifact_diffoscope_row_count`, `proof_extraction_theorem_count`, `state_space_catalog_row_count`, `causal_ablation_row_count`, `artifact_license_row_count`, `release_notes_row_count` | promoted canonical proof, finite-scope, license, and release-note artifacts |

`z_generate_manuscript_variables.py` writes `output/data/manuscript_variables.json` and resolves `output/manuscript/` for PDF rendering. Compose emits `{{token}}` placeholders; hydration is the single substitution boundary (fail-closed on unknown or single-brace `{token}` typos).

**Semantic gluing certificates:** `scripts/z_generate_manuscript_variables.py` writes
`output/data/sheaf_gluing_certificate.json`,
`output/data/sheaf_evidence_crosswalk.json`, and
`output/data/validation_dependency_graph.json` via
`src/manuscript/sheaf/semantic.py`. The certificate records section bindings,
shared GNN/ontology symbols, typed claim evidence, artifact producers, artifact
consumers, validation gates, and manuscript variables. `validate_manuscript`
fails if the certificate is missing, stale, or records cross-track disagreement.
`generate_integration_audit.py` writes producer, stale-artifact, token-provenance,
figure-source, claim-audit, scope-boundary, manuscript-staleness, and adversarial
audit reports. `generate_sheaf_tracks.py` is the canonical promotion producer: it
writes `output/data/sheaf_gluing_certificate.json`,
`output/data/validation_dependency_graph.json`,
`output/data/evidence_field_index.json`,
`output/reports/release_bundle_manifest.json`,
`output/data/theorem_traceability_matrix.json`,
`output/data/track_improvement_scope.json`, and the canonical replay, sensitivity,
uncertainty, counterexample, model-checking, interop, adversarial, provenance, and
blocked-scope artifacts. `validate_outputs` and `validate_manuscript` require the
canonical saved artifacts after regeneration; versioned live track IDs and
versioned public output paths are intentionally not part of the live contract.

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

**SI figures** (`figures.yaml`): `si_belief_entropy_curve`, `si_obs_action_trace`, `si_tmaze_actions` bound under `results_si_tmaze` with numbering declared in `section_figures`. **Sheaf layers figure:** `sheaf_layers_overview` (two-panel registry stack + heatmap) bound under `methods_sheaf` with its caption prefix and number from `figures.yaml`. **Appendix:** MI/actions and coverage heatmap captions are also source-backed from `figures.yaml`. **Front matter:** coverage page uses “Coverage overview.” caption without a figure number.

**Discussion sheaf tracks:** `discussion_outlook` binds `prose`, `simulation`, and `ontology` fragments with measured tokens.

**Extension artifacts:** `simulate_si_tmaze.py` writes
`output/data/si_policy_comparison.json`,
`output/data/pymdp_policy_posterior_grid.json`, and
`output/reports/pymdp_runtime_diagnostics.json`; `simulate_si_graph_world.py` writes
`output/data/si_graph_world_summary.json` and `output/data/si_graph_world_trace.json`;
`render_animation.py` writes a trace-derived multi-frame
`output/figures/si_belief_trajectory.gif` and
`output/data/animation_frame_deltas.json`. These are deterministic public
artifacts.

**Validation-spine tracks:** `generate_validation_spine.py` writes initial
provenance, replay, and counterexample support artifacts. `generate_sheaf_tracks.py`
then folds the strongest deterministic evidence into the canonical `provenance`,
`replay_matrix`, and `counterexample` sheaf tracks, plus the validation-spine
tracks added for `evidence_fields`, `release_bundle`, `theorem_traceability`, and
`gate_ergonomics`.

**Promoted roadmap tracks:** `generate_toy_sweep_tracks.py` writes sensitivity,
uncertainty, benchmark, measured policy-grid, EFE-availability, analytical-observable,
analytical-assumption, graph-world topology trace, and graph-world invariant
artifacts. `generate_formal_interop_tracks.py` writes finite model-checking, GNN
round-trip/lint, ontology profile/alias, and Lean theorem inventory artifacts.
`generate_integration_audit.py` writes manuscript-staleness and integration audit
artifacts. `generate_sheaf_tracks.py` consolidates the live canonical track
surface and removes legacy duplicate public artifacts. These tracks are live and
toy-only; `empirical_adapter` remains blocked rather than live.

Non-blocking follow-up scope is tracked in [`TODO.md`](TODO.md); keep current
publication claims confined to deterministic toy artifacts unless new measured
outputs are added and validated.

**Methods sheaf layers (main body):** `methods_sheaf` uses explicit `track_order` to place prose/formalism/visualization, provenance, counterexample, adversarial audit, evidence fields, release bundle, gate ergonomics, manuscript staleness, and generated layer tables. Layers overview figure via `visualization` / `section_figures`; tables via optional `layers` track / `layers_report` renderer with HTML markers `sheaf-layers:*`, including the generated track-improvement scope. Front-matter audit page [`manuscript/00_00_sheaf_coverage.md`](manuscript/00_00_sheaf_coverage.md) uses `section_figures.coverage_page` (no duplicate figure number vs appendix coverage figure).

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

**Visualizations** (`src/visualizations/`): `figure_registry.py` (YAML SSOT + `write_figure_registry_json`), `figure_helpers.py` (`styled_figure`), `figures_diagrams.py`, `lean_boundary.py`, `figures.py` (`FIGURE_GENERATORS`, 13 figures), `figures_sheaf_{payload,draw}.py`. `generate_all_figures()` emits `output/figures/figure_registry.json` for validation.

**Appendix proof:** `appendix_full_sheaf` binds the registry tracks required for the full proof row (all except optional `layers`) → `16_appendix_full_sheaf.md`. Registry size is injected from live counts rather than hand-authored here.

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
| `src/validation_spine/` | Provenance hashes, deterministic replay, and counterexample matrix artifacts |
| `src/roadmap_tracks/` | Promoted toy sweep, formal interop, integration-audit, and canonical sheaf-track artifacts |
| `gnn/*.gnn.md` | GNN source files |
| `lean/TemplateActiveInference/` | Lean witnesses — `build_lean` gate runs `lake build` when `lean/lakefile.lean` exists; absent Lean tree skips cleanly |
| `scripts/` | Thin orchestrators only (extension tracks delegate to `src/visualizations/animation.py`, `src/simulation/graph_world.py`) |

## Commands

```bash
uv run python scripts/compose_manuscript.py
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run python scripts/validate_outputs.py
```

## Parent docs

- Root [`AGENTS.md`](../../AGENTS.md)
- [Publishing guide](../../../docs/guides/publishing-guide.md) · [Zenodo DOI strategy](../../../docs/guides/zenodo-doi-strategy.md)
- [`tracks.yaml`](tracks.yaml)
