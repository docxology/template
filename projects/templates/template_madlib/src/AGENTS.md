# src

The `src/` package is the project-local generation engine. Keep it free of `infrastructure.*` imports so the domain logic remains portable and directly testable.

| Module | Role |
| --- | --- |
| `config.py` | Validate `manuscript/config.yaml` `madlib:` settings, including expanded manuscript-structure, design-principle, phase, evaluation, QA-probe, failure-mode, authoring-obligation, cover/visualization, and explicit/default-origin controls. |
| `tokens.py` | Expand slot declarations into deterministic token choices. |
| `composition.py` | Build conditional manuscript section bodies, Markdown evidence tables, and figure Markdown groups. |
| `analysis.py` | Thin orchestrator: `generate_artifacts` loads config, builds the token plan, and delegates to `analysis_fields`/`analysis_figures`/`analysis_reports`, returning the artifact-path map. |
| `analysis_fields.py` | Build the configured-field inventory and explicit/default origin counts from config plus token plan. |
| `analysis_figures.py` | Write the nine figure PNGs (cover overview plus eight interior figures) and the `figure_registry.json` entries. |
| `analysis_reports.py` | Write the JSON data artifacts and the Markdown summary/configured-field reports. |
| `manuscript_variables.py` | Emit the flat `{{TOKEN}}` map consumed by manuscript injection. |

Add tests for every schema or generation change before changing manuscript shells. Keep prose composition deterministic and sourced from config, token plan, or generated artifact state.

When Methods content changes, keep these surfaces aligned in the same change: `madlib.method_protocol`, `pipeline_phases`, `quality_probes`, `failure_modes`, `audit_rules`, `contribution_claims`, figure registry rows, manuscript variables, generated tables, and `data/claim_ledger.yaml`.

Preserve token-selection invariants in `tokens.py`: seed, slot name, category, ordinal, and ordered category inventory are the only token-choice inputs. Keep review-packet handoff language backed by generated data/report/figure artifacts, validation reports, and `output/reports/output_statistics.json`.
