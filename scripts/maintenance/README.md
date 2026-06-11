# Maintenance Scripts

Operator and repository-maintenance scripts for the template. These are thin
orchestrators that delegate to `infrastructure/` modules. They are **not** part
of the numbered build pipeline (`scripts/00_*.py`–`10_*.py`) and **not**
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

## Running

```bash
uv run python scripts/maintenance/<script>.py [args]
```

The repo sets `[tool.uv] package = false`, so it is never installed into the
venv; each script puts the repo root (`parents[2]` from here) on `sys.path`
before importing `infrastructure`.
