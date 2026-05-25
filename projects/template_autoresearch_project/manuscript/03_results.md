# Results

The generated loop selected `{{ACCEPTED_CANDIDATE_ID}}` after evaluating
`{{EVALUATED_CANDIDATE_COUNT}}` candidate(s) from a proposed set of
`{{CANDIDATE_COUNT}}`. The majority-class baseline reached
`{{BASELINE_ACCURACY}}` held-out accuracy, while the accepted candidate reached
`{{BEST_ACCURACY}}`, an absolute change of `{{ACCURACY_DELTA}}`. The candidate
budget exhausted flag is `{{BUDGET_EXHAUSTED}}`, which means the ledger records
at least one deferred proposal rather than expanding the run automatically.

The benchmark score is `{{BENCHMARK_SCORE}}`. That score is not a model-quality
claim by itself; it is a compact grading artifact for the methods contract:
metric improvement, budget compliance, offline execution, and accepted-candidate
recording. The candidate score figure is registered as @fig:ml_candidate_scores,
and the machine-readable candidate ledger is summarized in
@tbl:ml-candidate-ledger.

| Artifact | Role |
| --- | --- |
| `output/data/ml_task_results.json` | Dataset summary, baseline, evaluated candidates, accepted candidate, and metric delta |
| `output/data/ml_candidate_ledger.json` | Proposed, evaluated, accepted, rejected, and deferred candidate lifecycle records |
| `output/reports/ml_experiment_report.md` | Human-readable ML-loop experiment report |
| `output/reports/ml_benchmark_score.json` | Benchmark-style score for the ML-loop method contract |
| `output/figures/ml_candidate_scores.png` | Baseline and evaluated-candidate accuracy figure |

: Deterministic ML-loop candidate artifacts. {#tbl:ml-candidate-ledger}

The broader AutoResearch run also writes the reproducibility and review
surfaces in @tbl:autoresearch-loop.

| Artifact | Role |
| --- | --- |
| `output/data/autoresearch_plan.json` | Deterministic plan snapshot |
| `output/data/autoresearch_claims.json` | Local-artifact claim ledger |
| `output/data/research_program.json` | Human-authored program and budget controls |
| `output/data/idea_ledger.json` | Proposed, accepted, rejected, and deferred ideas |
| `output/data/run_ledger.json` | Replayable budget and stop-condition ledger |
| `output/data/review_decisions.json` | Required human review gate decisions |
| `output/data/benchmark_scores.json` | Benchmark-style task grading status |
| `output/reports/autoresearch_loop.md` | Human-readable loop report |
| `output/reports/autoresearch_readiness.json` | Strict readiness report |

: AutoResearch readiness and review artifacts. {#tbl:autoresearch-loop}

The final run supports `{{SUPPORTED_CLAIM_COUNT}}` manuscript-facing claim(s)
and checks `{{REQUIRED_ARTIFACT_COUNT}}` required artifact(s). The rendered
manuscript uses injected variables from generated data payloads, so the abstract
and results track the latest analysis run rather than hard-coded counts. The
final readiness status is `{{READINESS_STATUS}}`; generated review decisions are
recorded as deferred for human review rather than as self-approval.
