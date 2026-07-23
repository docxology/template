# scripts/maintenance/AGENTS.md

## Purpose

Operator and repository-maintenance orchestrators. **None of these run in the default `./run.sh` pipeline or CI** — they are run on demand by a maintainer. They are distinct from the canonical stage entrypoints under [`scripts/pipeline/`](../pipeline/) and from validation gates ([`scripts/gates/`](../gates/)).

## Modules

| Script | Delegates to | Purpose |
|--------|--------------|---------|
| `manage_workspace.py` | `infrastructure.project.workspace` | uv workspace status / add a package to a project |
| `show_project_info.py` | `infrastructure.project.info.collect_project_info`, `display_project_info` | Print metadata for a discovered project (standalone CLI; not invoked by the `run.sh` menu) |
| `render_working_projects.py` | `infrastructure.project.working_render` | Render private-sidecar `working/` projects on demand |
| `rerender_working_pdfs.py` | `infrastructure.project.working_render` | Re-render working-project PDFs with a PASS/PARTIAL/FAIL rubric |
| `organize_executive_outputs.py` | `infrastructure.reporting.run_executive_output_organization` | Tidy multi-project executive report outputs |
| `merge_test_supplements.py` | `infrastructure.validation.test_supplements.merge_supplements` | Merge pytest supplement files into a canonical module |
| `batch_cogsec_improve.py` | `infrastructure.core.source_improve` | Batch source-improvement orchestrator |
| `setup_pre_commit.py` | (subprocess `pre-commit install`) | Install / refresh the pre-commit hook set |
| `codegraph_local.py` | `infrastructure.project.codegraph` | Local CodeGraph index helper commands (optional; not a CI/publication dependency) |
| `refresh_artifact_manifests.py` | `infrastructure.core.pipeline.artifacts.snapshot_current_artifact_manifest` | Explicit integrity rebaseline for already-generated outputs; never claim its `current-output-snapshot` entries are stage provenance |
| `benchmark_health.py` | `infrastructure.core.health_benchmark` | Own clean-checkout serial/parallel health runs and fail unless gate parity, provenance, green status, and the latency criterion all hold |
| `rename_counts_doc.py` | (self-contained tree scan) | Guard that scans tracked text files for stale `canonical_facts.md` markers after the COUNTS.md rename; `--check` exits non-zero when any remain outside archived audits |

## Usage

```bash
uv run python scripts/maintenance/<script>.py [args]
```

`[tool.uv] package = false`, so each script puts the repo root (`parents[2]`
from this directory) on `sys.path` before importing `infrastructure`.

## See also

- [`scripts/`](../) — pipeline orchestration scripts
- [`scripts/gates/`](../gates/) — validation gate scripts
- [`scripts/README.md`](../README.md) — full scripts inventory
