# Maintenance Scripts

Operator and repository-maintenance scripts for the template. These are thin
orchestrators that delegate to `infrastructure/` modules. They are **not** part
of the canonical build pipeline (`scripts/pipeline/stage_*.py`) and **not**
validation gates (those live in [`scripts/gates/`](../gates/)).

## Scripts

| Script | Delegates to | Purpose |
|--------|--------------|---------|
| `manage_workspace.py` | `infrastructure.project.workspace` | uv workspace status / add a package to a project |
| `show_project_info.py` | `infrastructure.project.info` | Print metadata for a discovered project |
| `render_working_projects.py` | `infrastructure.project.working_render` | Render private-sidecar `working/` projects on demand |
| `rerender_working_pdfs.py` | `infrastructure.project.working_render` | Re-render working-project PDFs and classify PASS/PARTIAL/FAIL |
| `organize_executive_outputs.py` | `infrastructure.reporting` | Tidy multi-project executive report outputs |
| `merge_test_supplements.py` | `infrastructure.validation.test_supplements` | Merge pytest supplement files into a canonical module |
| `batch_cogsec_improve.py` | `infrastructure.core.source_improve` | Batch source-improvement orchestrator |
| `setup_pre_commit.py` | (subprocess) | Install / refresh the pre-commit hook set |
| `codegraph_local.py` | `infrastructure.project.codegraph` | Local CodeGraph index helper commands (optional, not a CI dependency) |
| `refresh_artifact_manifests.py` | `infrastructure.core.pipeline.artifacts` | Rebaseline integrity manifests after intentional targeted renders; records `current-output-snapshot`, not stage provenance, and methods audits report that distinction |
| `benchmark_health.py` | `infrastructure.core.health_benchmark` | Run serial/parallel clean-checkout health and write an acceptance manifest |
| `benchmark_tests.py` | `infrastructure.core.test_performance` | Run matched serial/parallel evidence for the infrastructure or public quick test lane |

## Running

```bash
uv run python scripts/maintenance/<script>.py [args]
```

For example, after targeted public-exemplar renders:

```bash
uv run python scripts/maintenance/refresh_artifact_manifests.py --all-public
```

The repo sets `[tool.uv] package = false`, so it is never installed into the
venv; each script puts the repo root (`parents[2]` from here) on `sys.path`
before importing `infrastructure`.
