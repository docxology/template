# Troubleshooting — Template Madlib

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Token `{{VAR}}` appears raw in output | Missing variable in `manuscript_variables.py` | Add the variable and re-run |
| Section not generated | Section switch in config.yaml is `false` | Set to `true` in `madlib.section_switches` |
| QA probes missing from manuscript | `quality_probes` list is empty in config | Add probes under `madlib.quality_probes` |
| Figure registry validation fails | Figure specs changed but registry not regenerated | Re-run `scripts/pipeline/stage_02_analysis.py` |
