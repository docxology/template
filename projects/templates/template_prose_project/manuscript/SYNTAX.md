# Manuscript Syntax Reference (prose_project)

Project-specific overlay on the canonical [`docs/guides/manuscript-semantics.md`](../../../../docs/guides/manuscript-semantics.md) — read that file first; this file documents **prose_project**-specific conventions.

The prose exemplar deliberately omits equations and figures-from-data; its job is to *evaluate* manuscripts, not produce numerical artefacts. The pipeline still emits three diagnostic figures (per-file word counts, readability metrics, citation density) into `output/figures/` for human inspection, but they are not embedded in the manuscript body — they are part of the review report.

## Citations

Pandoc-style only. Every citation key must resolve in [`references.bib`](references.bib).

```markdown
[@peng2011reproducible]
[@flesch1948new; @kincaid1975derivation; @gunning1952technique]
@strunk2000elements remains the canonical English-prose reference.
```

Pipeline behaviour:

* `bibliography.fail_on_missing: true` — a `[@key]` whose key is not in `references.bib` makes the `bibliography_consistency` check fail.
* `bibliography.fail_on_unused: false` — bib entries with no citations only produce warnings.

The [`citation_density_above_floor`](../src/pipeline/checks.py) check (`_check_citation_density` in `src/pipeline/checks.py`) enforces ≥ `prose.citation_density_min_per_1000` citations per 1000 words.

## Section labels

| File | Section H1 | Label |
|---|---|---|
| `00_abstract.md` | Abstract | `{#sec:abstract}` |
| `01_introduction.md` | Introduction | `{#sec:introduction}` |
| `02_methodology.md` | Methodology | `{#sec:methodology}` |
| `03_results.md` | Results | `{#sec:results}` |
| `04_conclusion.md` | Conclusion | `{#sec:conclusion}` |
| `05_pipeline_internals.md` | Pipeline Internals | `{#sec:pipeline_internals}` |
| `06_reproducibility.md` | Reproducibility | `{#sec:reproducibility}` |
| `99_references.md` | References | `{#sec:references}` |

Cross-section references in prose use `[@sec:methodology]`, never markdown filename links.

## Heading hierarchy rules

The prose pipeline checks two structural rules — keep them satisfied or expect failures:

1. **`every_file_has_h1`** — every section file begins with a single `# Title {#sec:short_name}` H1 (the `{#sec:…}` label syntax above is illustrative, not a real label).
2. **`no_skipped_heading_levels`** — never jump from `#` (H1) directly to `###` (H3); use `##` (H2) in between.

The Pandoc renderer uses `--number-sections`, so **never write manual numbers** like `## 2.1 Read`. Just write `## Read` and let Pandoc autonumber.

## `{{TOKEN}}` substitution

`scripts/z_generate_manuscript_variables.py` computes token values via `src/manuscript_variables.py::compute_variables()` and writes substituted copies of `manuscript/*.md` to `output/manuscript/` via `infrastructure.rendering.manuscript_injection.write_resolved_manuscript_tree()`. This file (`SYNTAX.md`), `AGENTS.md`, and `README.md` are excluded from `output/manuscript/` so their literal `{{TOKEN}}` examples are never substituted.

| Token | Source |
|---|---|
| `{{CONFIG_TITLE}}` | `config.yaml` `paper.title` |
| `{{TOTAL_WORDS}}` | sum of `metrics.word_count` |
| `{{TOTAL_SENTENCES}}` | sum of `metrics.sentence_count` |
| `{{TOTAL_PARAGRAPHS}}` | sum of `metrics.paragraph_count` |
| `{{AVG_GRADE_LEVEL}}` | weighted-average Flesch-Kincaid Grade Level |
| `{{AVG_READING_EASE}}` | weighted-average Flesch Reading Ease |
| `{{AVG_GUNNING_FOG}}` | weighted-average Gunning Fog Index |
| `{{CITATION_COUNT}}` | unique cited keys |
| `{{FILES_ANALYSED}}` | number of files in `manuscript_report.files` |
| `{{LONGEST_SECTION_WORDS}}` | max per-file word count |
| `{{SHORTEST_SECTION_WORDS}}` | min per-file word count |

Define new tokens in [`src/manuscript_variables.py`](../src/manuscript_variables.py) and they become available everywhere.

## Preamble

[`preamble.md`](preamble.md) loads the LaTeX packages required for tables, citations, and cross-references. The prose project does **not** load `algorithm2e`, `siunitx`, or `listings` — it has no equations, no algorithms, no code listings to typeset.

## See also

- [`../../../docs/guides/manuscript-semantics.md`](../../../../docs/guides/manuscript-semantics.md) — Repository-wide canonical semantics
- [`AGENTS.md`](AGENTS.md) — Substitution-marker registry and editing checklist
- [`../docs/output_conventions.md`](../docs/output_conventions.md) — What lands in `output/`
- [`../../../infrastructure/prose/SKILL.md`](../../../../infrastructure/prose/SKILL.md) — Underlying analysis API
- [`../../../infrastructure/reference/SKILL.md`](../../../../infrastructure/reference/SKILL.md) — Bibliography validation API
