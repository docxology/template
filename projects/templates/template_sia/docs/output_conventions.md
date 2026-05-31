# Output conventions — template_sia

| Path | Producer | Consumer |
| --- | --- | --- |
| `output/runs/run_{id}/gen_{n}/target_agent.py` | Loop (live or fixture) | Evaluation, inspection |
| `output/runs/run_{id}/gen_{n}/results.json` | `evaluate.py` | Reports, manuscript vars |
| `output/runs/run_{id}/gen_{n}/agent_execution.json` | Target step | `load_agent_execution()` |
| `output/runs/run_{id}/gen_{n}/improvement.md` | Feedback step | Context ledger |
| `output/runs/run_{id}/context.md` | Context ledger | Agent context (deterministic) |
| `output/runs/run_{id}/run_summary.json` | Loop runner | `z_generate_manuscript_variables.py` |
| `output/reports/sia_loop_report.md` | `src/reports.py` | Human review |
| `output/data/manuscript_variables.json` | Variables script | Debugging, tokens audit |
| `output/manuscript/*.md` | Injection pass | PDF renderer |
| `output/pdf/template_sia_combined.pdf` | Stage 05 | Validation, publication |

Working tree under `projects/templates/template_sia/output/` is gitignored. Tracked render-proof copies live under `output/templates/template_sia/` when copied by Stage 09.

Disposable: delete `output/` anytime; regenerate with the pipeline.
