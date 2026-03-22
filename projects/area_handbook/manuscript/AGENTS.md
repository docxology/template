# manuscript/ — area_handbook

## Sections (main numeric)

| File | Topic |
|------|--------|
| `01_abstract.md` | Scope and workflow summary |
| `02_introduction.md` | Living handbook rationale |
| `03a_methods_corpus.md` | Evidence model |
| `03b_methods_outline.md` | Chapter routing |
| `03c_methods_synthesis.md` | Scores, gaps, figures (coverage, by-theme, gap status) |
| `03d_methods_quality.md` | Corpus validation gates |
| `04_landscape.md` … `12_handbook_maintenance.md` | Domain chapters |
| `13_stakeholders_use_cases.md` | Audience and boundary objects |
| `14_appendix_corpus_schema.md` | YAML schema and output paths |

## Supplemental (`S01_` …)

| File | Topic |
|------|--------|
| `S01_limitations.md` | Scope limits, assumptions |
| `S02_worked_example_riverbend.md` | End-to-end traceability walkthrough |

## Other

| File | Topic |
|------|--------|
| `handbook_syntax.md` | Citations, figure paths, section naming (discovery: **other** bucket) |

## Figures

Analysis writes PNGs under `../output/figures/`. `scripts/02_generate_handbook_figure.py` also writes `figure_registry.json` (keys must match `\ref{fig:…}` / `{#fig:…}` labels) for `validate_figure_registry`.

| File | Label |
|------|--------|
| `handbook_evidence_coverage.png` | `fig:coverage` |
| `handbook_evidence_by_theme.png` | `fig:bytheme` |
| `handbook_section_gap_status.png` | `fig:gapstatus` |

## Citations

`references.bib` keys include: `bowker2005`, `edwards2010`, `gray2005`, `template2026`, `star1989`.

## Pipeline

Discovered by `infrastructure.rendering.manuscript_discovery.discover_manuscript_files`. Numeric prefixes sort in the main group; `S01_`–style files sort in the supplemental group; `handbook_syntax.md` sorts in the **other** group (lexicographic among non-main files).
