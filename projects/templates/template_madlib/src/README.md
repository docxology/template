# Source Package

Core generation logic for `template_madlib`.

| Module | Contract |
| --- | --- |
| `config.py` | Parses `madlib:` from `manuscript/config.yaml`; validates lexicon, slots, section conditions, section titles, narrative moves, method protocol, design principles, pipeline phases, evaluation criteria, QA probes, failure modes, authoring obligations, visualization controls, audit rules, and contribution claims; records explicit/default config paths. |
| `tokens.py` | Expands slots into deterministic token choices from seed, category, slot name, ordinal, and full category inventory. |
| `composition.py` | Builds multi-paragraph manuscript bodies plus section, configured-field, design-principle, pipeline-phase, protocol, contribution, audit, evaluation, QA-probe, failure-mode, authoring-obligation, provenance, title, token tables, and figure Markdown groups. Methods prose must explain digest construction, review scenario, explicit/default field origin, method invariants, slot-to-section allocation, figure evidence, claim-ledger alignment, validation gates, review-packet handoff, and fork migration from config plus `TokenPlan`. |
| `analysis.py` | Writes JSON/report/figure artifacts, cover overview, pipeline/allocation/provenance/gate figures, configured-field inventories, origin/coverage figures, and the figure registry. Analysis owns the visual and data evidence used by the generated Methods, Results, Configuration, Evaluation, and review-packet surfaces. |
| `manuscript_variables.py` | Builds the flat variable map consumed by manuscript injection. |

The important invariant is simple: config changes flow through source code into generated artifacts and hydrated manuscript variables. Generated Markdown in `output/manuscript/` is disposable.

When a fork changes the generation method, update `config.py` validation if the schema changes, `composition.py` body/table prose, `analysis.py` artifacts or figures, `manuscript_variables.py` exported placeholders, and tests in the same pass. Do not describe a new method step unless it has a config row, an evidence artifact or table, and a gate that can fail. Do not describe a review handoff unless the copied-output surface includes the data, reports, figures, validation results, and copy statistics needed to inspect it.

```bash
uv run pytest projects/templates/template_madlib/tests/ --cov=projects/templates/template_madlib/src --cov-fail-under=90
```
