# Results

The generated loop report is written to `output/reports/autoresearch_loop.md`.
The machine-readable payload is written to `output/data/autoresearch_loop.json`,
and manuscript variables are written to `output/data/manuscript_variables.json`.

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

The rendered manuscript uses injected variables from the same data payload, so
the abstract follows the latest analysis run instead of hard-coded counts.
