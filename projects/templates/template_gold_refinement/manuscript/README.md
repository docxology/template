# Manuscript

Source manuscript files for `template_gold_refinement`.

## Files

| File | Role |
|------|------|
| `00_abstract.md` | Abstract with purity summary |
| `01_introduction.md` | Introduction: ore to nine-nines |
| `02_methodology.md` | Methodology: the refinery pipeline |
| `03_results.md` | Results: purity progression and karat grading |
| `04_discussion.md` | Discussion: load-bearing vs rhetorical |
| `05_conclusion.md` | Conclusion: certification and forking |
| `06_reproducibility.md` | Reproducibility: seeded regeneration |
| `07_scope.md` | Scope: related work and limitations |
| `08_evaluation.md` | Evaluation: QA probes, audit rules, and integrity gates |
| `09_authoring_contract.md` | Authoring contract: human review and responsible forks |
| `config.yaml` | Paper metadata and gold_refinement block |
| `config.yaml.example` | Fork template |
| `preamble.md` | LaTeX preamble |
| `references.bib` | BibTeX bibliography |
| `layer_contract.yaml` | Layer boundary contract |

## Generated-variable discipline

Manuscript source files should contain prose, cross-reference labels, and
`{{TOKEN}}` placeholders. Generated numbers, figure blocks, formalism rows,
claim-support summaries, evidence-tier summaries, and figure-quality summaries
come from `src/manuscript_variables.py` and `output/data/manuscript_variables.json`.

Do not hard-code figure numbers, equation numbers, table numbers, generated
counts, support rates, evidence fact counts, or figure-quality totals in
manuscript prose. Use `[@fig:...]`, `[@eq:...]`, `[@tbl:...]`, and generated
variables so prerender, registry, evidence, and citation gates can detect drift.

## Visual QA text

Results and reproducibility sections intentionally describe
`output/reports/figure_quality_report.json`. That report is generated from
source-owned figure specs and records PNG/SVG presence, dimensions, nonblank
pixel checks, color variance, and registry parity. If a fork changes figures,
update `src/figures.py`, regenerate Stage 02, and let the manuscript consume
the refreshed variables rather than editing rendered Markdown.
