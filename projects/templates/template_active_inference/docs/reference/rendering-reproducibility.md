# Rendering and Reproducibility Contract

This exemplar has one rendering paradigm: authored fragments and configuration
produce deterministic data, figures, composed Markdown, hydrated Markdown, PDF,
web, and copied root outputs. Do not hand-edit generated artifacts to make a
claim pass; regenerate the producer that owns the artifact.

## Authored surfaces

- `manuscript/sections/imrad/**` contains editable section fragments.
- `manuscript/sheaf/tracks.yaml` declares fragment types, renderers, and order.
- `manuscript/sheaf/manifest.yaml` binds fragments to IMRAD rows.
- `tracks.yaml` declares pipeline tracks, gates, and extension artifacts.
- `figures.yaml` is the source of truth for figure ids, captions, alt text,
  widths, and section bindings.
- `manuscript/refs/labels.yaml` is intentionally absent; it was a stale second
  figure registry. Figure labels are declared only by `figures.yaml` and
  materialized in `output/figures/figure_registry.json`.
- `pymdp.yaml`, `domain_profile.yaml`, and `data/claim_ledger.yaml` define
  deterministic runtime, domain, and claim-evidence contracts.

## Generated artifacts

- `output/data/*.json` and `output/reports/*.json` are produced by project
  scripts and validation-spine modules.
- `manuscript/0*.md`, except hand-authored front/back matter, are composed from
  sheaf fragments by `scripts/compose_manuscript.py`.
- `output/manuscript/*.md` is hydrated from composed manuscript sections plus
  `output/data/manuscript_variables.json`.
- `output/figures/*` comes from `scripts/generate_figures.py` and
  `scripts/render_animation.py`.
- `output/pdf/*` and `output/web/*` are render outputs, not sources of truth.
- Root-level `output/templates/template_active_inference/**` is copied from the
  project-local `output/**` by the root pipeline.

## Single hydration boundary

The single hydration boundary is `scripts/z_generate_manuscript_variables.py`.
Composition may emit `{{token}}` placeholders, but only hydration substitutes
them. Unknown placeholders and single-brace token typos fail closed. Volatile
counts, run facts, semantic restrictions, and figure captions must enter through
`output/data/manuscript_variables.json`, never hard-coded prose.

## Producer order

Run producers in this order when refreshing the full reproducible surface:

```bash
uv run python scripts/compose_manuscript.py
uv run python scripts/run_analytical_sweep.py
uv run python scripts/simulate_si_tmaze.py
uv run python scripts/simulate_si_graph_world.py
uv run python scripts/compute_statistics.py
uv run python scripts/generate_figures.py
uv run python scripts/render_animation.py
uv run python scripts/generate_validation_spine.py
uv run python scripts/generate_toy_sweep_tracks.py
uv run python scripts/generate_formal_interop_tracks.py
uv run python scripts/generate_integration_audit.py
uv run python scripts/generate_sheaf_tracks.py
uv run python scripts/z_generate_manuscript_variables.py
uv run python scripts/generate_method_inventory.py
```

`generate_sheaf_tracks.py` is the canonical consolidation pass. It rewrites the
semantic certificate, dependency graph, provenance, replay, counterexample,
evidence-field, release-bundle, theorem-traceability, gate-index, diffoscope,
proof-extraction, state-space, causal-ablation, license, release-note,
proof-dependency, transition-table, ablation-sensitivity, release-attestation,
track-improvement, blocked-scope, section-status, and render-log artifacts.

## Figure rendering contract

Every figure id must exist in `figures.yaml`, have a generator in
`src/visualizations/figures.py`, write through `figure_io.save_figure_png`, and
appear in `output/figures/figure_registry.json`. Figure captions and alt text may
use hydration tokens, but figure numbering belongs to pandoc-crossref. Reused
figures must use unlabeled references rather than duplicate labels.
The appendix theorem-traceability graph and causal-ablation heatmap are generated
from JSON rows and validated by the same figure registry contract as the main
figures.

## Sheaf reproducibility

The sheaf claim is finite and falsifiable:

- registry tracks must be known and typed by renderer;
- manifest bindings must resolve to existing fragments or generated renderers;
- coverage must have zero gray cells on a clean tree;
- semantic gluing must record shared symbols, claim evidence, artifact
  producers, consumers, validation gates, and manuscript variables;
- every promoted artifact must have a producer, a bound manuscript track, a
  typed claim, a validation restriction, and a negative-control test.

## Root output parity

Project-local outputs are authoritative during generation. After a root pipeline
run, verify copied root output parity as well:

```bash
./run.sh --project template_active_inference --pipeline --core-only
uv run python scripts/validate_outputs.py
```

The semantic and release-bundle reports allow render-deferred PDF/web rows before
copy, but final acceptance must inspect both `output/**` inside the project and
`../../output/templates/template_active_inference/**` from the repository root.
