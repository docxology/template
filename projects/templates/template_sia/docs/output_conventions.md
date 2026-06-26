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

The public template tracks this project-local `output/` tree and the copied
`output/templates/template_sia/` tree as release artifacts when files stay below
the 50 MB public output ceiling.

Regenerate `output/` with the pipeline after producer changes instead of editing
rendered artifacts by hand.
