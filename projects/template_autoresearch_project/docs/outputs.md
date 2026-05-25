# Outputs

Running `template_autoresearch_project` creates machine-readable data,
human-readable reports, manuscript variables, and review material.

Core data:

| Path | Role |
| --- | --- |
| `output/data/autoresearch_plan.json` | Composed plan from project profile, experiment plan, and pipeline DAG |
| `output/data/autoresearch_loop.json` | Full loop payload with config, stages, claims, metrics, and paths |
| `output/data/autoresearch_claims.json` | Evidence-grounded generated claims |
| `output/data/autoresearch_stage_matrix.csv` | Tabular stage status for spreadsheet review (`status` is `declared`, not execution proof) |
| `output/data/autoresearch_review_packet.json` | Machine-readable human review packet |
| `output/data/manuscript_variables.json` | Variables injected into the manuscript |

Figures:

| Path | Role |
| --- | --- |
| `output/figures/autoresearch_stage_matrix.png` | Visual stage, claim, and artifact readiness matrix |
| `output/figures/figure_registry.json` | Registered figure metadata for validation |

Reports:

| Path | Role |
| --- | --- |
| `output/reports/autoresearch_loop.json` | Report copy of the loop payload |
| `output/reports/autoresearch_loop.md` | Human-readable loop report |
| `output/reports/autoresearch_review_packet.md` | Human review packet with required actions |
| `output/reports/autoresearch_summary.md` | Short project summary |
| `output/reports/autoresearch_readiness.json` | Structured readiness validation result |
| `output/reports/autoresearch_readiness.md` | Human-readable readiness validation result |
| `output/reports/evidence_registry.json` | Evidence registry for artifact-backed facts |
| `output/reports/artifact_manifest.json` | Artifact manifest with sizes and checksums |

Pipeline rendering also produces manuscript, PDF, HTML, and slide outputs when
the standard `run.sh` path reaches render and copy stages.
