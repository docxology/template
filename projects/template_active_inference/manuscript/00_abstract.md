# Abstract

This public exemplar binds **{{pipeline_track_count}} pipeline tracks** — Lean, analytical Python, pymdp sophisticated inference, GNN, ontology concordance, visualizations, and the sheaf manuscript composer — declared in [`tracks.yaml`](../tracks.yaml). Flat manuscript sections follow an **IMRAD outline** (Introduction, Methods, Results, Discussion, plus appendix) assembled from **{{sheaf_track_count}} sheaf fragment types** registered in [`manuscript/sheaf/tracks.yaml`](sheaf/tracks.yaml).

The first page ([`00_00_sheaf_coverage.md`](00_00_sheaf_coverage.md)) shows a **{{imrad_manifest_rows}}-row coverage matrix** ({{imrad_group_count}} IMRAD group headers and {{composed_section_count}} composed subsections, including a full-track appendix proof) regenerated from the live manifest at compose time.

The T-maze demo aligns with [pymdp sophisticated_inference examples](https://github.com/infer-actively/pymdp/tree/main/examples/experimental/sophisticated_inference).

Measured invariant checks: {{invariants_passed}} / {{invariants_total}} passed. SI planning horizon: {{si_tmaze_policy_len}} steps.
