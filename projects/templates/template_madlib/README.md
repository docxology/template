# Template Madlib — Deterministic Token-Injection Exemplar

`template_madlib` is a public canonical exemplar for configuration-driven manuscript generation. It uses a Mad Lib style vocabulary surface, but the point is not novelty prose. The point is to show how conditional text, section titles, method steps, design principles, QA probes, authoring obligations, configured-field origins, token provenance, and publication boundaries can be generated from tracked config plus project-local source code.

`manuscript/config.yaml` owns the `madlib:` schema: seed, lexicon, slots, section switches, section titles, narrative moves, method protocol, design principles, operational phases, evaluation criteria, QA probes, failure modes, authoring obligations, visualization controls, audit rules, and contribution claims. The Python package expands that schema into token choices, configured-field origin inventories, evidence tables, reports, a figure registry, nine generated figure artifacts (the cover overview plus eight interior manuscript figures), and a hydrated IMRAD manuscript under `output/manuscript/`. The current method protocol is intentionally broad: it covers schema ingestion, review-scenario declaration, field-origin tracking, lexicon governance, digest construction, invariant review, slot expansion, section-condition handling, body composition, evidence-table assembly, claim-ledger alignment, figure registry generation, manuscript hydration, render validation, review-packet assembly, copy validation, and fork-migration documentation.

## Publication and rendering

- Standalone GitHub: [docxology/template_madlib](https://github.com/docxology/template_madlib)
- Latest GitHub release: [v0.1.1](https://github.com/docxology/template_madlib/releases/tag/v0.1.1)
- Zenodo concept DOI: [10.5281/zenodo.20786638](https://doi.org/10.5281/zenodo.20786638)
- Latest Zenodo version DOI: [10.5281/zenodo.20932025](https://doi.org/10.5281/zenodo.20932025) ([record](https://zenodo.org/records/20932025))
- Canonical renderer: [docxology/template](https://github.com/docxology/template) with `--project templates/template_madlib`
- Tracked outputs: [`output/`](output/) in this project and `output/templates/template_madlib/` in the monorepo; public output files above 50 MB stay out of git.

To regenerate this exemplar from the public monorepo:

```bash
git clone https://github.com/docxology/template
cd template
uv sync
./run.sh --project templates/template_madlib --pipeline --core-only
uv run python scripts/04_validate_output.py --project templates/template_madlib
uv run python scripts/05_copy_outputs.py --project templates/template_madlib
```

Standalone repositories are publication mirrors for source, DOI metadata, and
tracked rendered artifacts. Use the monorepo above when you need the full shared
infrastructure, pipeline stages, or cross-template validation.

## When to use this template

Use this template when you need **configuration-driven manuscript generation with auditable token provenance, conditional section structure, explicit/default field visibility, failure-boundary reporting, and a reviewer-visible authoring contract**: lexicon categories, section titles, narrative moves, method steps, design principles, pipeline phases, evaluation criteria, QA probes, failure modes, authoring obligations, visualization controls, audit rules, and slots are declared in YAML; `src/` deterministically expands those declarations; and the manuscript receives large-grain `{{TOKEN}}` bodies only after the source code has generated the supporting artifacts. It is not a natural-language quality benchmark or a claim that random word substitution creates scholarship.

## Project Shape

| Surface | Responsibility |
| --- | --- |
| `manuscript/config.yaml` | Declares the Madlib schema, manuscript titles, narrative moves, method protocol, design principles, pipeline phases, evaluation criteria, QA probes, failure modes, authoring obligations, visualization controls, audit rules, lexicon categories, and slots. |
| `src/config.py` | Validates `madlib:` and rejects malformed sections, empty required lexicons, bad protocol/design/phase/evaluation/probe/failure/obligation rows, malformed visualization controls, and invalid composition depth; records explicit and defaulted config paths. |
| `src/tokens.py` | Uses seeded digest selection so a fixed config produces a stable token plan and config edits produce reviewable changes. |
| `src/composition.py` | Builds multi-paragraph IMRAD, evaluation, reproducibility, limitation, scope, and authoring-contract bodies plus Markdown evidence tables and figure groups from config plus token plan. |
| `src/analysis.py` | Thin orchestrator: `generate_artifacts` loads config, builds the token plan, and delegates to the sibling `analysis_*` modules, returning the artifact-path map. |
| `src/analysis_fields.py` | Builds the configured-field inventory and explicit/default origin counts. |
| `src/analysis_figures.py` | Writes the nine figure PNGs (cover overview, token density, injection flow, section allocation, provenance map, quality-gate matrix, configured-field matrix, section heatmap, origin summary) and the figure registry. |
| `src/analysis_reports.py` | Writes the JSON data artifacts (token inventory, section plan, configured-field inventory, injection trace) and the Markdown summary/configured-field reports. |
| `src/manuscript_variables.py` | Emits the flat `{{TOKEN}}` replacement map consumed by manuscript injection. |
| `manuscript/*.md` | Keeps author-readable section shells; generated prose belongs only under `output/manuscript/`. |

## Method Protocol Contract

Treat `madlib.method_protocol` as the source of the generated Methods section, not as decorative metadata. A fork that changes the generation method should update the protocol rows, `pipeline_phases`, `quality_probes`, `failure_modes`, `audit_rules`, `contribution_claims`, and the project claim ledger in the same change. Each method row should name the action, the evidence artifact, and the output it creates; each pipeline phase should name its input, transformation, output, and guard.

The exemplar's digest method is deterministic by construction: the seed, slot name, category, ordinal, and ordered category inventory are hashed before selecting a token. The configured-field inventory then separates explicit YAML paths from loader defaults, and the slot-to-section allocation records where each token enters the manuscript. Methods prose, evidence tables, cover image, pipeline figures, registry rows, and validation gates all point back to those same source-owned facts.

The method now treats review operations as first-class outputs. A reviewer packet is not just the combined PDF or HTML page; it includes hydrated Markdown, web output, slides, figures, JSON data, reports, validation results, and copy statistics. In path terms, the handoff includes `output/manuscript`, `output/pdf`, `output/web`, `output/slides`, `output/figures`, `output/data`, `output/reports`, and `output/reports/output_statistics.json`. Token-selection invariants are also explicit: only seed, slot name, category, ordinal, and ordered category inventory should change token choices. Renderer state, file-copy order, and hand-edited output are outside the token-selection method.

Forks that add domain claims need additional domain validators and claim-ledger entries before they can claim domain evidence. Changing vocabulary alone does not make the generated manuscript empirically validated, reader-ready, or publication-ready.

## Fork Migration Checklist

Before a fork turns the exemplar into a domain report, update these surfaces together:

- `madlib.method_protocol`, `pipeline_phases`, `quality_probes`, `failure_modes`, `audit_rules`, and `contribution_claims`.
- `src/config.py` when the fork adds, removes, or changes schema fields, defaults, or malformed-value behavior.
- `src/composition.py` when the generated Methods prose or evidence tables change.
- `src/analysis.py` when new method artifacts, reports, figures, or registry rows are needed.
- Stage 04 validators or project-local validators when the fork introduces evidence that generic render checks cannot inspect.
- `tests/` so method rows, generated prose, artifacts, validators, registry coverage, review-packet surfaces, and unresolved-token scans can fail.
- `data/claim_ledger.yaml` so each local claim, non-claim, or domain claim has evidence.
- README/manuscript docs so reviewers know how to inspect generated Markdown, PDF, HTML, slides, figures, data, reports, validation results, and `output/reports/output_statistics.json`.

## Generated Evidence

Stage 02 writes:

- `output/data/token_inventory.json`
- `output/data/section_plan.json`
- `output/data/configured_field_inventory.json`
- `output/data/manuscript_variables.json`
- `output/reports/injection_trace.json`
- `output/reports/madlib_summary.md`
- `output/reports/configured_field_summary.md`
- `output/figures/madlib_cover_overview.png`
- `output/figures/token_density.png`
- `output/figures/token_injection_flow.png`
- `output/figures/section_token_allocation.png`
- `output/figures/provenance_trace_map.png`
- `output/figures/quality_gate_matrix.png`
- `output/figures/configured_field_matrix.png`
- `output/figures/section_configuration_heatmap.png`
- `output/figures/field_origin_summary.png`
- `output/figures/figure_registry.json`

The hydrated manuscript includes Abstract, Introduction, Methods, Results, Discussion, Configuration, Evaluation, Reproducibility, Limitations, Scope, Authoring Contract, and References. Methods is deliberately long because it is the exemplar's main contribution: it binds schema validation, review-scenario declaration, explicit/default field tracking, deterministic token planning, invariant review, slot-to-section allocation, conditional section hydration, visual audit figures, claim-ledger alignment, operational phases, review-packet assembly, evidence artifacts, validation gates, and failure-mode checks into one source-owned protocol. Evaluation adds explicit QA probes, while the Authoring Contract states what a human reviewer or downstream fork must still do before treating generated prose as reader-ready.

Stage 03 renders PDF, HTML, and slides from the hydrated manuscript. Stage 04 verifies PDF validity, Markdown, figure registry, evidence registry, design overlays, and artifact manifest. Stage 05 copies ignored generated deliverables into `output/templates/template_madlib/`.

## Boundaries


## Template integrity

- Forward backlog: [`TODO.md`](TODO.md).
- Copy-and-customize config: [`manuscript/config.yaml.example`](manuscript/config.yaml.example).
- Project validation: `uv run pytest projects/templates/template_madlib/tests/ --cov=projects/templates/template_madlib/src --cov-fail-under=90`.
- Repo drift validation: `uv run python scripts/check_template_drift.py --strict`.

Output Markdown, PDF, HTML, slides, figures, reports, and copied deliverables are disposable. Regenerate them through Stages 02-05 after source edits; do not hand-edit `output/` artifacts to make a method or documentation claim pass review.

<!-- foam-orphan-nav:start (auto-managed: links sub-docs so they are reachable) -->

## Directory & sub-document map

Navigation links to in-tree documents (keeps them discoverable):

- [data](data/AGENTS.md)
- [Data](data/README.md)
- [docs](docs/AGENTS.md)
- [Documentation](docs/README.md)
- [scripts](scripts/AGENTS.md)
- [Scripts](scripts/README.md)
- [src](src/AGENTS.md)
- [Source Package](src/README.md)
- [tests](tests/AGENTS.md)
- [Test Patterns](tests/PATTERNS.md)
- [Tests](tests/README.md)

<!-- foam-orphan-nav:end -->
