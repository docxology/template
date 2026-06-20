# src

The `src/` package is the project-local generation engine. Keep it free of `infrastructure.*` imports so the domain logic remains portable and directly testable.

| Module | Role |
| --- | --- |
| `config.py` | Validate `manuscript/config.yaml` `madlib:` settings, including expanded manuscript-structure, design-principle, phase, evaluation, QA-probe, failure-mode, authoring-obligation, cover/visualization, and explicit/default-origin controls. |
| `tokens.py` | Expand slot declarations into deterministic token choices. |
| `composition.py` | Build conditional manuscript section bodies, Markdown evidence tables, and figure Markdown groups. |
| `analysis.py` | Write data, report, configured-field inventory, cover, figure artifacts, and the figure registry from the token plan and config schema. |
| `manuscript_variables.py` | Emit the flat `{{TOKEN}}` map consumed by manuscript injection. |

Add tests for every schema or generation change before changing manuscript shells. Keep prose composition deterministic and sourced from config, token plan, or generated artifact state.

When Methods content changes, keep these surfaces aligned in the same change: `madlib.method_protocol`, `pipeline_phases`, `quality_probes`, `failure_modes`, `audit_rules`, `contribution_claims`, figure registry rows, manuscript variables, generated tables, and `data/claim_ledger.yaml`.

Preserve token-selection invariants in `tokens.py`: seed, slot name, category, ordinal, and ordered category inventory are the only token-choice inputs. Keep review-packet handoff language backed by generated data/report/figure artifacts, validation reports, and `output/reports/output_statistics.json`.
