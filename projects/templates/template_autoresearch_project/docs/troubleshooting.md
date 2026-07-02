# Troubleshooting — AutoResearch Project

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `readiness_valid = False` | Some required artifact is empty or missing | Run the full analysis stage, check `output/data/` for expected files |
| ML candidate budget exhausted | `ml.max_candidates` too low for the search space | Increase in `autoresearch.yaml` or narrow the candidate space |
| Token `{{METRIC}}` appears raw | Variable not injected in `manuscript_variables.py` | Add the variable binding and re-run `z_generate_manuscript_variables.py` |
| Evidence registry validation fails | `claim_ledger.yaml` references a non-existent artifact | Update the `artifact_path` to the real output location |
| Human review required but absent | `human_review.yaml` missing or incomplete | Create the review file with `approved: false` as a baseline |
| Security artifacts missing | Security stage not run | Run `scripts/02_run_analysis.py` which writes local security profile |
| Figure registry missing entries | New figure added without updating `manuscript_variables.py` | Add figure variable, update tests, re-run analysis |
