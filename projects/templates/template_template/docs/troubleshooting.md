# Troubleshooting — Template Meta-Project

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Published module count differs from `infrastructure/` listing | Introspection not re-run after adding/removing a subpackage | Re-run `generate_manuscript_metrics.py` |
| `${VARIABLE}` appears raw in rendered manuscript | Variable missing from `metrics.py` or injection script not run | Add the metric key and re-run injection |
| Architecture figure shows stale data | `generate_architecture_viz.py` not re-run | Re-run the figure generation script |
| Slide output missing | Slide renderer not invoked | Run `scripts/pipeline/stage_03_render.py` with slides config enabled |
| Comparative matrix empty | `figure_comparative_matrix.py` failed to find exemplar data | Check that `discover_projects()` returns the expected list |
| Web output missing | HTML render not configured | Check `manuscript/config.yaml` for web output settings |
| `check_template_drift.py --strict` fails | This exemplar's structure or claims drifted from the live repo scan | Run from repo root: `uv run python scripts/audit/check_template_drift.py --strict` and address the reported drift |
