# Sheaf composition package (`src/manuscript/sheaf/`)

Deterministic glue from `manuscript/sheaf/manifest.yaml` + `manuscript/sheaf/tracks.yaml` into flat `manuscript/NN_*.md` sections, with a B/W/G coverage matrix and heatmap.

## Module map

| Module | Public API |
| --- | --- |
| `models.py` | `TrackSpec`, `SheafSection`, `coverage_cell_symbol`, `COVERAGE_COLORS`, … |
| `registry.py` | `load_track_registry(path) -> TrackRegistry`, `track_order_for_section(...)` |
| `manifest.py` | `load_manifest(path, *, project_root) -> SheafManifest` |
| `renderers.py` | `RENDERERS`, `_GENERATED_RESOLVERS`, `resolve_track_body(...)`, `validate_renderer_specs` |
| `compose.py` | `compose_section(...)`, `compose_all_sections(...)`, `validate_manifest(...)` |
| `coverage.py` | `build_coverage_matrix(...)`, `load_sheaf_coverage_context(...)`, `emit_coverage_artifacts(...)`, … |
| `layers_report.py` | `render_sheaf_layers_markdown(project_root)` + table helpers |
| `counts.py` | `structural_counts(project_root)` for registry-backed tokens (incl. `sheaf_law_count`, `sheaf_laws_verified`) |
| `laws.py` | `verify_sheaf_laws(project_root) -> SheafLawReport`, `sheaf_law_violations(manifest, registry)`, `SheafLaw`, `SHEAF_LAW_COUNT` |
| `report.py` | `write_coverage_page`, `build_coverage_report`, heatmap config |

## Sheaf laws (`laws.py`)

The composer *performs* gluing; `laws.py` *verifies the axioms it assumes*, turning "sheaf" from notation into a falsifiable claim over the IMRAD base poset (`introduction ≺ methods ≺ results ≺ discussion ≺ appendix`, with `group ⊒ section`).

| Law | Verifies |
| --- | --- |
| `POSET` | IMRAD chain order; compose order monotone in block rank; every section's block has a group row |
| `PRESHEAF` | bound tracks ∈ registry; strict total compose order; local order is the monotone restriction of the global order |
| `SEPARATION` | `section → output_name` is injective (distinct locals → distinct global positions) |
| `GLUING` | compose order is a linear extension of the poset; each block contiguous; each section glues once |
| `TYPING` | renderer registered + fragment suffix ∈ renderer's accepted suffixes (generated renderers type-exempt) |
| `COMPOSITIONALITY` | every fragment file is private to one section (composition is a coproduct) |

`verify_sheaf_laws` is invoked inside `validate_manifest(...)` under `--strict`: a violation becomes an error-level `ManifestIssue` and aborts composition. **Discipline:** every law is paired with a negative control in [`../../../tests/test_sheaf_laws.py`](../../../tests/test_sheaf_laws.py) — a single mutation that breaks the law, proven to be caught — so the gate binds the laws' *content*, not their shape. Scope: axioms on a finite base, **not** sheaf cohomology.

## Generated renderers

| Renderer id | When used | Output |
| --- | --- | --- |
| `section_figures` | `visualization` track bound | Markdown from `figures.yaml` `section_figures` |
| `layers_report` | `layers` track bound (e.g. `methods_sheaf`) | Registry + binding matrix tables + legend |

`compose_section` calls `resolve_track_body()` for every track — no section-id special cases.

## Coverage colors

| Color | Status | Meaning |
| --- | --- | --- |
| `black` | `present` | Track bound in manifest and fragment file exists |
| `white` | `absent` | Track not bound for that section (not an error) |
| `gray` | `missing` | Track bound but fragment file absent |

`emit_coverage_artifacts` writes `output/data/sheaf_coverage_matrix.json` only. Heatmap PNG and coverage page come from `ensure_coverage_artifacts` during `generate_all_figures` (or CLI `--coverage-heatmap`). Sheaf figure implementation: [`../../visualizations/figures_sheaf.py`](../../visualizations/figures_sheaf.py).

## Semantic gluing modules

The semantic gluing certificate — cross-track disagreement checks the structural
sheaf laws do not cover, plus the JSON certificate and its writers/validators —
is split into focused modules. `semantic.py` is the public entrypoint;
`semantic_core.py` is a backward-compatible facade re-exporting the same names so
existing `from manuscript.sheaf.semantic_core import X` imports keep working.

| Module | Public API | Depends on (intra-package) |
| --- | --- | --- |
| `semantic_maps.py` | `SEMANTIC_SCHEMA`, `SEMANTIC_RESTRICTION_LANES`, `ARTIFACT_PRODUCERS`, `ARTIFACT_GATES`, `ARTIFACT_CONSUMERS` | — (leaf constants) |
| `semantic_restrictions.py` | `_load_json`, `_configured_analysis_scripts`, `_gnn_symbols`, `_lean_status`, `_policy_comparison_restrictions`, `_policy_posterior_restrictions`, `_runtime_diagnostics_restrictions`, `_graph_world_restrictions`, `_pymdp_hash_restrictions`, `_animation_frame_count`, `_restriction_lane_assignments`, `_restriction_lane_summaries`, `_proof_obligation_rows`, `_expected_symbol_gaps`, `_section_ontology_symbols` | `semantic_maps` |
| `semantic_evidence.py` | `build_evidence_crosswalk`, `build_validation_dependency_graph`, `validate_configured_artifact_producers`, `SEMANTIC_ARTIFACT_SOURCE_PATHS`, `SEMANTIC_PAYLOAD_PATHS`, `_section_records`, `_claim_records`, `_semantic_artifact_sources`, `_semantic_payloads`, `_semantic_track_rows`, `_semantic_shared_symbols`, `_canonical_restriction_snapshot` | `coverage`, `semantic_maps`, `semantic_restrictions` |
| `semantic_issues.py` | `semantic_gluing_issues(project_root) -> list[str]` | `coverage`, `semantic_evidence`, `semantic_restrictions` |
| `semantic_refresh.py` | `_refresh_hydrated_manuscript`, `_refresh_artifact_contract_outputs`, `_refresh_animation_outputs` | — (late imports only) |
| `semantic_certificate.py` | `build_semantic_gluing_certificate`, `write_semantic_gluing_certificate` | `coverage`, `semantic_evidence`, `semantic_issues`, `semantic_maps`, `semantic_refresh`, `semantic_restrictions` |
| `semantic_gluing_outputs.py` | `write_semantic_gluing_outputs`, `validate_semantic_gluing`, `_stable_artifact_graph`, `_stable_certificate_fields`, `_semantic_lane_summary_issues` | `semantic_certificate`, `semantic_evidence`, `semantic_issues`, `semantic_maps`, `semantic_refresh`, `semantic_restrictions` |
| `semantic_core.py` | facade re-exporting the public surface above | `semantic_certificate`, `semantic_evidence`, `semantic_gluing_outputs`, `semantic_issues` |
| `semantic.py` | public entrypoint (`__all__` for the sheaf package) | `semantic_core`, `semantic_maps` |

Cross-module imports sit at the top of each file. Late (in-function) imports are
used only to break genuine cycles with `roadmap_tracks.*`, `validation_spine`,
`gates.*`, `visualizations.animation`, `manuscript.refresh`, and
`manuscript.sheaf.status`, matching the pre-split behavior. `_semantic_payloads`
reads payloads through `json_io.load_json` (missing/invalid → `{}`), while
`semantic_issues` / `validate_semantic_gluing` keep `semantic_restrictions._load_json`
(fail-closed on malformed JSON) for the inputs they gate on.

## Commands

```bash
uv run python scripts/compose_manuscript.py
uv run python scripts/compose_manuscript.py --validate-only --strict
```

## Parent docs

- [`manuscript/sheaf/AGENTS.md`](../../../manuscript/sheaf/AGENTS.md) — YAML registries
- [`../../AGENTS.md`](../../AGENTS.md) — source package overview
- [`../../../AGENTS.md`](../../../AGENTS.md) — project overview
