# template_active_inference

📦 **Archived on Zenodo.** The [Zenodo concept DOI for template_active_inference](https://doi.org/10.5281/zenodo.20417021) always resolves to the latest version; the current release **v0.3.1** is the [Zenodo version DOI for v0.3.1](https://doi.org/10.5281/zenodo.20693424). Each Zenodo deposit links back to its matching [GitHub release](https://github.com/docxology/template_active_inference/releases). Cite via the concept DOI or [`CITATION.cff`](CITATION.cff).

Public exemplar: **sheaf-composed** Active Inference manuscript with configurable
multi-track sections. The live surface is declared in [`tracks.yaml`](tracks.yaml),
[`manuscript/sheaf/tracks.yaml`](manuscript/sheaf/tracks.yaml), and
[`figures.yaml`](figures.yaml); generated artifacts and gates, not prose lists,
define the current contract.

## Run via the template monorepo

This exemplar lives at `projects/templates/template_active_inference/` in the public
[docxology/template](https://github.com/docxology/template) repository.
**Tests, analysis, PDF rendering, and CI all run through that monorepo** —
clone it, run `uv sync` at the repository root, then:

```bash
./run.sh --project templates/template_active_inference --pipeline --core-only
# or: uv run python scripts/execute_pipeline.py --project templates/template_active_inference --core-only
```

Several exemplars also publish standalone GitHub/Zenodo releases for citation;
those mirrors are outputs of this pipeline. The monorepo remains the canonical
build and render surface.

## When to use this template

Use this template when **several independent research tracks must compose into
one manuscript whose claims stay consistent where the tracks overlap** — here:
a closed-form analytical oracle, a pymdp simulation harness, a Lean
formalization boundary, and shared GNN/ontology notation. Every section of the
paper is a typed fragment bound to one or more tracks, and machine-checked
composition laws (not an editor's eyeball) prove the fragments glue into a
single coherent document. If your project is single-method, start from
[`template_code_project`](../template_code_project/) instead; for the full
roster see
[`projects/AGENTS.md`](../../AGENTS.md#permanent-canonical-exemplars-and-optional-search-add-on).

## Why sheaf composition?

The problem: N tracks evolve independently (an analyst edits the closed-form
derivation while a simulation run regenerates posterior tables), yet the
manuscript must remain ONE document with no contradictions at the seams.
"Sheaf" here means exactly what the code enforces — a coverage presheaf over
the IMRAD section poset with law-verified gluing, not sheaf cohomology:

- **Locality** — each section×track binding is validated in isolation
  (fragment exists, renderer type-checks).
- **Gluing** — sections compose in a strict linear extension of the IMRAD
  order; every composing section appears exactly once.
- **Separation** — distinct sections cannot collide on one output file.
- **Semantic restriction** — symbols shared across tracks (e.g. the Bernoulli
  entropy value) are cross-checked in
  `output/data/sheaf_gluing_certificate.json`, so overlap consistency is an
  artifact, not a hope.

The six laws (poset, presheaf, separation, gluing, typing, compositionality)
live in [`src/manuscript/sheaf/laws.py`](src/manuscript/sheaf/laws.py), each
with a negative-control test that proves the law actually fires. See
[`src/manuscript/sheaf/README.md`](src/manuscript/sheaf/README.md) for the
engine's module map.

## Adding a track

1. Declare the track in
   [`manuscript/sheaf/tracks.yaml`](manuscript/sheaf/tracks.yaml) — id,
   `order` (global compose position), `renderer`, `label`, `optional` flag.
2. Bind it to sections in
   [`manuscript/sheaf/manifest.yaml`](manuscript/sheaf/manifest.yaml)
   (`tracks: {your_track: relative/fragment/path}` per section).
3. Create the fragment files under `manuscript/sections/imrad/<section>/`.
4. Validate the laws and coverage:
   `uv run python scripts/compose_manuscript.py --validate-only --strict`.
5. For a *validated* track (producer + artifact + gate + negative control),
   follow the seven-step promotion checklist in [`TODO.md`](TODO.md).

## Repository orientation

- [`docs/conceptual-foundations.md`](docs/conceptual-foundations.md) — the
  full intellectual grounding: Active Inference and EFE, cellular sheaves
  over the IMRAD poset, semantic gluing, the Lean 4 boundary, GNN/AIO
  notation contracts, and further reading.
- [`ISA.md`](ISA.md) — the project's Ideal State Artifact (design record and
  criteria history).
- [`TODO.md`](TODO.md) — backlog and the track promotion rule (a capability is
  live only when producer, artifact, manuscript consumer, claim evidence,
  semantic restriction, validation gate, and negative control all exist).
- [`STANDALONE.md`](STANDALONE.md) — how to copy this project out of the
  monorepo and run it independently (the sheaf engine under
  `src/manuscript/sheaf/` is deliberately generic; the registries are the
  bespoke part).
- [`AGENTS.md`](AGENTS.md) — module map and agent-facing contracts.

## Quick start

From the template repository root:

```bash
uv sync --directory projects/templates/template_active_inference --extra dev
cd projects/templates/template_active_inference
```

From this project root:

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
uv run python scripts/run_full_verification.py
```

> Runtime: the full suite is slow (~15-25 min serial) — real pandoc/xelatex
> rendering and artifact-generation/gate tests dominate, so a quiet console for
> several minutes is expected, not a hang. For a fast inner loop, scope with
> `-k` (e.g. `uv run pytest tests/ -k "not gate and not figure" --no-cov`).

From repo root:

```bash
uv run python scripts/01_run_tests.py --project templates/template_active_inference
./run.sh --project templates/template_active_inference --pipeline --core-only
```

## Sheaf composition

Tracks are declared in [`manuscript/sheaf/tracks.yaml`](manuscript/sheaf/tracks.yaml) (order, renderer, optional). Sections bind fragments in [`manuscript/sheaf/manifest.yaml`](manuscript/sheaf/manifest.yaml). The composer merges them into flat `manuscript/0*.md` files for the PDF pipeline.

The first manuscript page ([`manuscript/00_00_sheaf_coverage.md`](manuscript/00_00_sheaf_coverage.md)) shows a **B/W/G heatmap** of section × track coverage (black = present, white = absent, gray = missing binding). Compose writes `output/data/sheaf_coverage_matrix.json` only; `generate_figures.py` renders the heatmap PNG and regenerates the coverage page via `ensure_coverage_artifacts`.

Hydration writes a semantic sheaf certificate at `output/data/sheaf_gluing_certificate.json`.
It also writes `output/data/sheaf_evidence_crosswalk.json` and
`output/data/validation_dependency_graph.json`. Together these artifacts bind shared
GNN/ontology symbols, typed claims, artifact producers, validation gates, and manuscript
variables so the project validates semantic agreement, not only coverage shape.
The promoted validation-spine and canonical roadmap artifacts cover provenance,
replay, counterexamples, toy sweeps, uncertainty summaries, benchmark rows,
finite model-checking witnesses, interop reports, semantic gluing, dependency
graphs, evidence-field indexing, release-bundle parity, theorem traceability,
gate ergonomics, scholarship source mapping, visualization-quality and statistical-bridge auditing,
track-lane promotion mapping, artifact-contract indexing, local security-posture auditing,
artifact diffing, Lean proof extraction, finite state-space
catalogs, causal ablations, artifact license checks, release-note evidence,
track-improvement scope, and adversarial/scope audits. Live track IDs are stable
canonical names; future work improves those tracks rather than adding `_vN`
siblings.

Section [`16_appendix_full_sheaf.md`](manuscript/16_appendix_full_sheaf.md) binds the appendix manifest row as a composability proof; live counts are injected through manuscript variables, not hand-authored in this README. Optional `layers` is methods-only; `animation` is bound in the appendix row as a sheaf fragment.

The reproducible rendering contract is documented in
[`docs/reference/rendering-reproducibility.md`](docs/reference/rendering-reproducibility.md):
authored fragments/configs generate deterministic data, figures, composed
Markdown, hydrated Markdown, PDF/web outputs, and copied root outputs through one
hydration boundary.
Visualization quality is checked as generated evidence, not prose: the audit
joins render metrics, source maps, figure hashes, section bindings, and
per-figure claim lanes in `output/data/figure_source_map.json` and
`output/reports/visualization_quality_audit.json`. The same audit now enforces
the shared typography/layout tokens from `figures.yaml`, rejects raw
font-size literals in figure generators, and classifies auxiliary visual outputs
that are intentionally outside the numbered manuscript registry.
Scholarship quality is checked the same way: `output/data/scholarship_source_matrix.json`
is rederived from bibliography entries, manuscript citation sections, sheaf
tracks, manifest sections, scope-boundary text, and evidence artifacts before a
source row can count as connected.
Security posture is also a generated contract:
`output/reports/security_posture_audit.json` separates enforced local controls
from deferred production-only obligations, scans tracked project source/config
surfaces for high-risk secret patterns, and drives
`output/figures/security_posture_map.png`.
The cross-artifact contract is centralized in
`output/data/artifact_contract_index.json`: each row binds producer, configured
script, pipeline/sheaf lanes, manuscript consumers, claim predicates,
validators, negative controls, freshness status, and copied-root parity. Its
publication figure, `output/figures/artifact_contract_map.png`, makes that
contract inspectable in the methods and appendix sheaf.

```bash
uv run python scripts/compose_manuscript.py --list-tracks
uv run python scripts/compose_manuscript.py --section methods_analytical --tracks prose,formalism
uv run python scripts/compose_manuscript.py --validate-only --strict
```

Per-section overrides: `track_order`, `include_tracks`, `exclude_tracks`. See [`AGENTS.md`](AGENTS.md).

## pymdp anchor

T-maze sophisticated inference uses planning horizon `policy_len` from measured `si_tmaze_summary.json` (see manuscript variables). `simulate_si_tmaze.py` also writes `si_policy_comparison.json`, `pymdp_policy_posterior_grid.json`, and `pymdp_runtime_diagnostics.json`; the last file captures the known third-party JAX static-array warning and fails validation on unexpected construction warnings. Reference: [pymdp sophisticated_inference examples](https://github.com/infer-actively/pymdp/tree/main/examples/experimental/sophisticated_inference). Logs: `output/logs/pymdp_runs.jsonl`.

## Pipeline tracks

See [`tracks.yaml`](tracks.yaml). **Pipeline:** required tracks are declared
there, including core analytical/pymdp/formal/notation/visual tracks plus the
canonical validation and audit producers. **Sheaf registry:** fragment types live
in [`manuscript/sheaf/tracks.yaml`](manuscript/sheaf/tracks.yaml); the appendix
binds the full proof row except `layers`, which is methods-only. Thin scripts in
[`scripts/`](scripts/) delegate to `src/` and write deterministic local artifacts
under `output/`; `scripts/README.md` names the current producers and
`scripts/validate_outputs.py` checks their generated contracts.

Non-blocking future work is tracked in [`TODO.md`](TODO.md); current publication claims remain confined to deterministic toy Active Inference artifacts.

## Method inventory

Every Python `def` and `class` under `src/` and `scripts/` is documented in the
generated reference [`docs/reference/method-inventory.md`](docs/reference/method-inventory.md).
Regenerate it after method, script, or module changes, then check it before
reporting verification status:

```bash
uv run python scripts/generate_method_inventory.py --check
```

## Documentation verification

Run the documentation and artifact contract checks from this project root:

```bash
uv run python scripts/check_documentation_contract.py --check
uv run python scripts/run_full_verification.py
```

`run_full_verification.py` runs:

- preflight contract seeding:
  `compose_manuscript.py --validate-only --strict`, `z_generate_manuscript_variables.py`,
  `generate_figures.py`, `validate_outputs.py`, `check_documentation_contract.py --check`
- chunked verification batches for gate-heavy modules
- full `pytest` pass with coverage gate (`--cov=src --cov-fail-under=90`)
- postflight contract checks immediately after the full pass

The inventory distinguishes inline docstrings from inventory fallbacks, so missing
docstrings remain visible without bloating internal helper code.
