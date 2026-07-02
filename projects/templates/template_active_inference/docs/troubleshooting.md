# Troubleshooting — Active Inference

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Sheaf composition fails | Track registry and manifest are out of sync | Re-run `generate_sheaf_tracks.py` |
| Figure registry validation fails | Figures added but `figures.yaml` not updated | Update figure specs and re-run |
| Lean gate missing | `lean` binary not on PATH | Install Lean or skip with `--skip-lean` |
| Analytical/simulation mismatch | Tracks disagree on shared claims | Run cross-track validation tests |
