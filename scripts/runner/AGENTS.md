# scripts/runner/ — Pipeline Execution Runners

## Purpose

This subpackage holds **pipeline execution entry points** — scripts that
orchestrate one or many projects through the numbered pipeline stages.

## Scripts

| Script | Purpose |
|--------|---------|
| `execute_pipeline.py` | Single-project pipeline runner; delegates to `infrastructure.core.pipeline.PipelineExecutor` |
| `execute_multi_project.py` | Multi-project pipeline runner (serial; `--parallel` for process pool) |
| `run_matrix.py` | Reproducible project × stage matrix runner; reads `run.config`, resolves projects + orders stages canonically |
| `bundle_executable.py` | Executable-bundle stage (opt-in `bundle` tag); delegates to `infrastructure.publishing.executable_bundle.bundle_project` |
| `archive_publication.py` | Archival publication stage (opt-in `archival` tag); mirrors a project's executable bundle to Zenodo / Software Heritage / IPFS via `infrastructure.publishing.archival` (dry-run unless `--commit`; exit 2 when the bundle is absent) |
| `repro_bundle.py` | Reproduction-bundle `build`/`verify` thin wrapper forwarding to `infrastructure.publishing.repro_bundle` |

## Shared modules (not runners)

| Module | Purpose |
|--------|---------|
| `exit_codes.py` | Canonical `ExitCode` IntEnum naming the shared orchestrator exit-code contract (`SUCCESS=0`, `FAILURE=1`, `SKIP=2`, `VALIDATION_FAILED=3`, `MISSING_DEPENDENCY=4`); importing changes no behavior |
| `mcp_server_template.py` | Thin launcher for the template's stdio MCP server (equivalent to `python -m infrastructure.mcp_server`); opt-in agent surface, intentionally not part of the default pipeline/CI |

## Bootstrap pattern

Each script uses `parents[2]` to reach the repo root from `scripts/runner/`:

```python
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
```

## Usage

```bash
# Run full pipeline for one project
uv run python scripts/runner/execute_pipeline.py --project my_project

# Run all projects (serial)
uv run python scripts/runner/execute_multi_project.py

# Run all projects in parallel
uv run python scripts/runner/execute_multi_project.py --parallel

# Run reproducible stage matrix
uv run python scripts/runner/run_matrix.py
```

## See also

- [`scripts/pipeline/`](../pipeline/) — individual numbered stage scripts
- [`scripts/AGENTS.md`](../AGENTS.md) — full scripts inventory
- `./run.sh` — the interactive menu that delegates into these runners
