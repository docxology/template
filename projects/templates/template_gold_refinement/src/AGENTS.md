# src/ — Gold Refinement Domain Logic

## Overview

The `src/` directory contains the importable domain logic for the gold-refinement
exemplar. The refinery pipeline (`refinery.py`, `purity.py`) models the five
metallurgical stages; the mega-madlib engine (`config.py`, `composition.py`)
handles deterministic token injection; `assay.py` validates claims against
evidence; `formalisms.py` owns equation-backed formal claims; `integrity.py`
owns source-tiered risk and evidence models; `pipeline_policy.py` owns the
secure-pipeline and optional LLM-review gates; `domain_adapter.py` translates
domain metrics into the refinery purity scale; the `figures/` package owns all technical
visualization specs and quality reports; `manuscript_variables.py`
generates all `{{TOKEN}}` values; `coercion.py` normalizes loosely-typed config
values; `cover_visualization.py` renders the cover art; `dashboard.py` builds
the self-contained HTML metrics dashboard; and `security_assay.py` models
threat/standard/evidence-surface security-assay records.

## Layer Contract

`src/` must not import `infrastructure.*`. All infrastructure coupling belongs
in `scripts/` (thin orchestrators).

## Modules

| Module | Role |
|--------|------|
| `refinery.py` | Five-stage pipeline (ore → smelting → assaying → cupellation → certification) with monotone purity enforcement |
| `purity.py` | Karat grading (9K–24K), nine-nines certification, purity formatting |
| `config.py` | Mega-madlib config schema: lexicon, slots, section conditions, narrative moves |
| `composition.py` | Deterministic token selection via seeded SHA-256 digest |
| `assay.py` | Claim-evidence validation (the assaying stage) |
| `evidence.py` | Project-local contribution-claim registry and claim-ledger alignment |
| `formalisms.py` | Auto-numbered equation registry, formalism table rows, and traceability rows |
| `integrity.py` | Source-tiered integrity dimensions, residual-risk scores, and evidence-tier rows |
| `pipeline_policy.py` | Steganography profile parsing and optional LLM-review gating |
| `domain_adapter.py` | Domain metric translation and stage-remap profile loading |
| `figures/` | Figure subpackage: `_common` (specs + helpers), `graphs` (DiGraph builders), `charts` (bar/line charts), `diagrams` (graph/matrix diagrams), `registry` (registry + quality report + all-figures orchestrator); facade `__init__` preserves the public API |
| `manuscript_variables.py` | Generates all `{{TOKEN}}` values for manuscript injection |
| `coercion.py` | Loosely-typed config-value coercion (`coerce_bool` and siblings) |
| `cover_visualization.py` | Renders the project's cover art from `figures/_common` specs and integrity/formalism data |
| `dashboard.py` | Self-contained HTML dashboard: refinery metrics, purity progression, token distribution, evidence-registry status |
| `security_assay.py` | `SecurityAssayRecord` — threat / standard / evidence-surface / validator / claim-boundary rows |

## Key Design Rules

- Purity must increase monotonically across stages (`assert_monotone_increase`)
- Token selection is deterministic: same seed + lexicon = same plan
- Every `{{TOKEN}}` in manuscript source must be produced by `generate_variables()`
- Config owns all prose choices (lexicon, slots, narrative moves)
- `manuscript/config.yaml` also owns the secure-pipeline `steganography` block and the optional `llm` review gate
- `domain_profile.yaml` owns the stage-remap profile, benchmark rubric, and analogy-boundary notes
- Figure labels, paths, captions, and visual encodings must come from
  `FIGURE_SPECS`; do not duplicate registry metadata in scripts or manuscript
  prose.
- Every generated figure must be saved as PNG and SVG, registered in
  `figure_registry.json`, and measured in `figure_quality_report.json`.
- Graph figures should expose topology through source-owned builder functions
  so tests can assert node and edge counts without reading pixels.
- Keep project-local claim support in `claim_support_registry.json`; reserve
  `evidence_registry.json` for the shared template evidence validator.
