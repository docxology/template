# Source Package

Core generation logic for `template_madlib`.

| Module | Contract |
| --- | --- |
| `config.py` | Parses `madlib:` from `manuscript/config.yaml`; validates lexicon, slots, section conditions, section titles, narrative moves, method protocol, design principles, pipeline phases, evaluation criteria, QA probes, failure modes, authoring obligations, visualization controls, audit rules, and contribution claims; records explicit/default config paths. |
| `tokens.py` | Expands slots into deterministic token choices from seed, category, slot name, ordinal, and full category inventory. |
| `run.py` | Builds a `MadlibRun` session (config + token plan + sections + field counts) consumed by analysis and variable generation. |
| `composition.py` | Re-exports section bodies, tables, and figure markdown from `composition_*` modules. |
| `composition_helpers.py` | Shared composition helpers and disabled-section prose. |
| `composition_tables.py` | Markdown evidence tables for protocol, phases, probes, audit rules, and field inventories. |
| `composition_sections.py` | Conditional IMRAD section bodies and title variables. |
| `composition_figures.py` | Section figure-group markdown wired through `figure_specs`. |
| `figure_specs.py` | Registry of conditional figures; writes PNGs and supplies markdown groups. |
| `markdown_tables.py` | Report-oriented markdown table bundles for manuscript variables. |
| `analysis.py` | Writes JSON/report/figure artifacts via `build_run()`; owns visual and data evidence for Methods, Results, Configuration, Evaluation, and review-packet surfaces. |
| `analysis_fields.py` | Configured-field inventory and origin statistics. |
| `analysis_figures.py` | Figure PNG writers and registry entries. |
| `analysis_reports.py` | JSON artifacts and Markdown summary reports. |
| `manuscript_variables.py` | Builds the flat variable map consumed by manuscript injection. |

The important invariant is simple: config changes flow through source code into generated artifacts and hydrated manuscript variables. Generated Markdown in `output/manuscript/` is disposable.

When a fork changes the generation method, update `config.py` validation if the schema changes, the relevant `composition_*` / `figure_specs` prose, `analysis_*` artifacts or figures, `manuscript_variables.py` exported placeholders, and tests in the same pass. Do not describe a new method step unless it has a config row, an evidence artifact or table, and a gate that can fail. Do not describe a review handoff unless the copied-output surface includes the data, reports, figures, validation results, and copy statistics needed to inspect it.

```bash
uv run pytest projects/templates/template_madlib/tests/ --cov=projects/templates/template_madlib/src --cov-fail-under=90
```
