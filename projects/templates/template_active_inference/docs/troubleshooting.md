# Troubleshooting — Active Inference

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Sheaf composition fails | Track registry and manifest are out of sync | Re-run `generate_sheaf_tracks.py` |
| Figure registry validation fails | Figures added but `figures.yaml` not updated | Update figure specs and re-run |
| Lean gate missing | `lake`/`lean` binaries not on PATH | Install the Lean 4 toolchain (see `lean/lean-toolchain` / `lean/AGENTS.md`) so `lake build` succeeds; the gate only auto-skips when `lean/lakefile.lean` itself is absent (`src/gates/lean.py::lean_project_present`) — there is no CLI flag to skip it while the lakefile is present |
| Analytical/simulation mismatch | Tracks disagree on shared claims | Run cross-track validation tests |
