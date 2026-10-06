# Troubleshooting — Active Inference

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Sheaf composition fails | Track registry and manifest are out of sync | Re-run `generate_sheaf_tracks.py` |
| Figure registry validation fails | Figures added but `figures.yaml` not updated | Update figure specs and re-run |
| Lean gate blocked | Missing declarations, elan, or the exact installed toolchain | Install the exact source-owned Lean toolchain (see `lean/lean-toolchain` / `lean/AGENTS.md`) explicitly. Missing declarations or tools return blocked75; they cannot grant a successful skip. Invalid declarations return2. |
| Analytical/simulation mismatch | Tracks disagree on shared claims | Run cross-track validation tests |
