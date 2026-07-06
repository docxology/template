# src

The `src/` package is the project-local generation engine. Keep it free of `infrastructure.*` imports so the domain logic remains portable and directly testable.

| Module | Role |
| --- | --- |
| `config.py` | Validate `manuscript/config.yaml` `madlib:` settings, including expanded manuscript-structure, design-principle, phase, evaluation, QA-probe, failure-mode, authoring-obligation, cover/visualization, and explicit/default-origin controls. |
| `tokens.py` | Expand slot declarations into deterministic token choices. |
| `run.py` | `MadlibRun` session plus `build_run()` — single load of config, token plan, sections, and field inventory for artifact and variable generation. |
| `composition.py` | Thin re-export facade over the split composition modules (stable import surface for tests and callers). |
| `composition_helpers.py` | Shared prose helpers, disabled-section bodies, figure markdown fragments. |
| `composition_tables.py` | Markdown evidence tables (protocol, phases, probes, audit, fields, tokens, …). |
| `composition_sections.py` | Conditional IMRAD section bodies and section title variables. |
| `composition_figures.py` | Figure-group markdown for Methods, Results, Configuration, and Evaluation sections. |
| `figure_specs.py` | Declarative conditional figure registry; drives PNG writes and markdown groups from config. |
| `markdown_tables.py` | `artifact_markdown_tables()` for report-oriented table bundles (used by variables path). |
| `analysis.py` | Orchestrates `build_run()`, writes JSON/report/figure artifacts, returns artifact path map. Public export: `generate_artifacts` only. |
| `analysis_fields.py` | Configured-field inventory and explicit/default origin counts. |
| `analysis_figures.py` | Cover and interior figure PNG writers plus figure registry rows. |
| `analysis_reports.py` | JSON data artifacts and Markdown summary/configured-field reports. |
| `artifact_writers.py` | Registry-driven JSON and Markdown artifact writers (`write_core_artifacts`). |
| `manuscript_variables.py` | Flat `{{TOKEN}}` map via `build_run()` and `markdown_tables` (no import from `analysis`). |

Add tests for every schema or generation change before changing manuscript shells. Keep prose composition deterministic and sourced from config, token plan, or generated artifact state.

When Methods content changes, keep these surfaces aligned in the same change: `madlib.method_protocol`, `pipeline_phases`, `quality_probes`, `failure_modes`, `audit_rules`, `contribution_claims`, figure registry rows, manuscript variables, generated tables, and `data/claim_ledger.yaml`.

Preserve token-selection invariants in `tokens.py`: seed, slot name, category, ordinal, and ordered category inventory are the only token-choice inputs. Keep review-packet handoff language backed by generated data/report/figure artifacts, validation reports, and `output/reports/output_statistics.json`.
