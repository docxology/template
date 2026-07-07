# Troubleshooting — AutoResearch Project

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `readiness_valid = False` | Some required artifact is empty or missing | Run the full analysis stage, check `output/data/` for expected files |
| ML candidate budget exhausted | `ml.max_candidates` too low for the search space | Increase in `autoresearch.yaml` or narrow the candidate space |
| Token `{{METRIC}}` appears raw | Variable not injected in `src/manuscript/manuscript_tokens_core.py` or `manuscript_tokens_ml.py` (`manuscript_variables.py` is only the re-export facade) | Add the variable binding there and re-run `z_generate_manuscript_variables.py` |
| Evidence registry validation fails | `claim_ledger.yaml` references a non-existent artifact | Update the `artifact_path` to the real output location |
| Human review required but absent | `human_review.yaml` missing or incomplete | Create the review file with `approved: false` as a baseline |
| Security artifacts missing | Security stage not run | Run `scripts/pipeline/stage_02_analysis.py` which writes local security profile |
| Figure registry missing entries | New figure added without updating `src/manuscript/manuscript_tokens_figures.py` | Add figure variable, update tests, re-run analysis |
