## Compose contract

Each manifest row in `manuscript/sheaf/manifest.yaml` binds fragment tracks from `manuscript/sheaf/tracks.yaml`. A track supplies a renderer, compose order, label, optional flag, general paper role, and paper-specific use statement; the composer flattens the binding set into one Markdown section for PDF and web output.

The operational claim is auditable binding: analytical, simulation, pymdp, visualization, Lean, GNN, ontology, scholarship, and optional media fragments attach to each IMRAD row under [@eq:coverage_cell] (**P** present, **—** unbound, **M** missing). This is an applied local-to-global consistency contract in the spirit of cellular sheaf and sheaf-signal-processing work [@curry2014sheaves; @robinson2014topological], but instantiated here as a finite manuscript artifact gate.

## Coverage and figures

[@fig:sheaf_layers_overview] summarizes {{sheaf_track_count}} fragment types and their IMRAD bindings. Generated tables below list every track definition and section×track binding at compose time. The visualization track has its own generated quality audit at `output/reports/visualization_quality_audit.json`: {{visualization_quality_rendered_count}} / {{visualization_quality_figure_count}} registered figures are rendered, {{visualization_quality_source_mapped_count}} are source-mapped, and {{visualization_quality_accessibility_count}} have sufficient alt-text/caption metadata; the all-quality flag is `{{visualization_quality_all_ok}}`. The stricter paper-integration gates also require declared visual/evidence roles (`{{visualization_intent_metadata_complete}}`), artifact-backed paper claims (`{{visualization_paper_claims_complete}}`), and at least one section binding per registered figure (`{{visualization_figures_section_bound}}`). The same audit marks {{visualization_statistics_backed_count}} figures as statistically backed by generated data or report artifacts, with bridge status `{{visualization_statistics_bridge_ok}}`; `output/data/statistical_visualization_bridge.json` expands that into {{statistical_visualization_bridge_row_count}} figure-source-scholarship rows with connected status `{{statistical_visualization_bridge_all_connected}}`, manuscript-reference status `{{statistical_visualization_bridge_all_referenced}}`, and visualization-bound reference status `{{statistical_visualization_bridge_references_visualization_bound}}`.

## Compose commands

```bash
uv run python scripts/compose_manuscript.py
uv run python scripts/compose_manuscript.py --validate-only --strict
```

Each run emits `output/data/sheaf_coverage_matrix.json` and regenerates coverage artifacts. Partial compose (`--section`) is draft-only; the matrix always reflects the full manifest. Coverage totals appear on [@sec:sheaf_coverage]; discussion scope is in [@sec:discussion_outlook].

## Law verification

`--validate-only --strict` runs the structural gate before any fragment is glued. Beyond per-cell coverage, it invokes the sheaf-law oracle (`verify_sheaf_laws`, `src/manuscript/sheaf/laws.py`), which checks {{sheaf_law_count}} axioms — poset, presheaf functoriality, separation, gluing, typing, and compositionality — and reports {{sheaf_laws_verified}}/{{sheaf_law_count}} satisfied for the current manifest. A violation is raised as an error-level issue and aborts the build, so a malformed manifest (a section colliding on an output file, an off-chain block, a mistyped fragment, a fragment shared between sections) can never compose. The formal statements are in the formalism block below; the negative-control suite (`tests/test_sheaf_laws.py`) proves each check is falsifiable.

The semantic layer is separate from those structural laws. `output/data/sheaf_gluing_certificate.json` records cross-track symbols, typed claim evidence, artifact sources, and manuscript-variable restrictions; validation fails when the analytical, pymdp, GNN, ontology, Lean, visualization, or manuscript tracks disagree about a shared symbol or measured claim. The visualization-quality audit is one of those restrictions, so a missing source map, missing statistical bridge source, missing hash, underspecified caption, non-RGB render, or undersized figure breaks the same semantic sheaf contract that checks statistics and theorem witnesses. [@fig:semantic_gluing_graph] renders this gluing graph: the configured producers, the generated evidence artifacts, and the validation consumers that read each shared symbol.
