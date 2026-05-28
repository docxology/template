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

## Commands

```bash
uv run python scripts/compose_manuscript.py
uv run python scripts/compose_manuscript.py --validate-only --strict
```

## Parent docs

- [`manuscript/sheaf/AGENTS.md`](../../../manuscript/sheaf/AGENTS.md) — YAML registries
- [`../../AGENTS.md`](../../AGENTS.md) — project overview
