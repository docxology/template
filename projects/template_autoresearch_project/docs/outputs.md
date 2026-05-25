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
| `output/data/research_program.json` | Human-authored research program, autonomy level, budget, and edit allowlist |
| `output/data/idea_ledger.json` | Proposed, accepted, rejected, and deferred research ideas plus candidates |
| `output/data/run_ledger.json` | Replay ledger with budget use and stop condition |
| `output/data/review_decisions.json` | Required human review gate decisions |
| `output/data/benchmark_scores.json` | Benchmark-style grading status for configured tasks |
| `output/data/ml_task_results.json` | Fixed-seed dataset summary, baseline, candidates, accepted candidate, and metric delta |
| `output/data/ml_candidate_ledger.json` | Candidate lifecycle ledger with proposed, evaluated, accepted, rejected, and deferred states |
| `output/data/manuscript_variables.json` | Variables injected into the manuscript |

Figures:

| Path | Role |
| --- | --- |
| `output/figures/autoresearch_stage_matrix.png` | Visual stage, claim, and artifact readiness matrix |
| `output/figures/ml_candidate_scores.png` | Baseline and evaluated-candidate held-out accuracy chart |
| `output/figures/figure_registry.json` | Registered figure metadata for validation |

Reports:

| Path | Role |
| --- | --- |
| `output/reports/autoresearch_loop.json` | Report copy of the loop payload |
| `output/reports/autoresearch_loop.md` | Human-readable loop report |
| `output/reports/autoresearch_review_packet.md` | Human review packet with required actions |
| `output/reports/autoresearch_summary.md` | Short project summary |
| `output/reports/ml_experiment_report.md` | Human-readable deterministic ML-loop report |
| `output/reports/ml_benchmark_score.json` | Grading output for metric improvement, budget compliance, offline execution, and selection status |
| `output/reports/autoresearch_readiness.json` | Structured readiness validation result |
| `output/reports/autoresearch_readiness.md` | Human-readable readiness validation result |
| `output/reports/benchmark_readiness_smoke.json` | Deterministic grading output for the exemplar benchmark task |
| `output/reports/evidence_registry.json` | Evidence registry for artifact-backed facts |
| `output/reports/artifact_manifest.json` | Artifact manifest with sizes and checksums |

Pipeline rendering also produces manuscript, PDF, HTML, and slide outputs when
the standard `run.sh` path reaches render and copy stages.
