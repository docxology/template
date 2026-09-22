# `template_experiment_tree/manuscript/`

Manuscript sources and publication configuration for the living-record
exemplar. The paper is a deterministic projection of the committed
experiment tree — every number is a token hydrated from tree state.

## Sections

| File | Role |
|---|---|
| [`config.yaml`](config.yaml) | Single source of truth for publication metadata and render settings; `config.yaml.example` is the fork template. |
| [`preamble.md`](preamble.md) | Shared preamble injected at render time. |
| [`00_abstract.md`](00_abstract.md) | Abstract with `{{EXP_*}}` substitution markers. |
| [`01_introduction.md`](01_introduction.md) | Why research logs rot and how a frozen-node tree fixes the coupling. |
| [`02_methodology.md`](02_methodology.md) | Status ladder and run_command contract. |
| [`03_results.md`](03_results.md) | Answered nodes and winners per round. |
| [`04_discussion.md`](04_discussion.md) | Dead ends (negative-result registry) and frozen preregistrations. |
| [`99_references.md`](99_references.md) | Pandoc bridge to `references.bib`. |
| [`references.bib`](references.bib) | Hand-curated bibliography (OpenResearch inspiration note; preregistration references). |

## Tokens

Every `{{EXP_*}}` marker resolves from the tree via
`scripts/z_generate_manuscript_variables.py`; a token with no tree backing
fails hydration. Never hand-type a result.

| Marker | Source |
|---|---|
| `{{EXP_TOTAL}}` `{{EXP_ANSWERED}}` `{{EXP_FROZEN}}` `{{EXP_PROVISIONAL}}` | Node counts by status (`src/template_experiment_tree/report.py` `summarize`). |
| `{{EXP_WINS}}` `{{EXP_LOSSES}}` `{{EXP_DEAD_ENDS}}` | Outcome counts over answered nodes. |
| `{{EXP_MAX_DEPTH}}` `{{EXP_WINNERS_PER_ROUND}}` | Tree shape and per-round winners. |
| `{{EXP_SECTIONS_RESULTS}}` `{{EXP_SECTIONS_IN_PROGRESS}}` `{{EXP_SECTIONS_DEAD_ENDS}}` | Generated markdown bodies from `flatten_sections`. |

## Editing

```bash
uv run python projects/templates/template_experiment_tree/scripts/z_generate_manuscript_variables.py
```

Claim boundary: no claim may cite a run that is not an answered node in the
tree. See [AGENTS.md](AGENTS.md) for editing rules; repo-wide policy is
[`../AGENTS.md`](../AGENTS.md).