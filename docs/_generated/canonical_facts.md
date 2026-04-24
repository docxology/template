# Canonical Factsheet

**Generated from live repo state on 2026-04-24 (UTC).** Last measured runs: `generate_active_projects_doc.py`, `pytest` discovery suite; `fep_lean` counts below are from the last full `projects/fep_lean` tree measurement (see commands).

This file aggregates verifiable facts from discovery scripts, CI configuration, and test execution. Human-written documentation should link here rather than duplicate lists or numbers.

## Project Roster

**Active projects** — authoritative list: [`active_projects.md`](active_projects.md) (from `discover_projects()`). This checkout: `code_project` only.

**In-progress projects** (`projects_in_progress/`):

- act_inf_metaanalysis
- biology_textbook
- cogant
- cognitive_integrity
- template

Regenerate [`active_projects.md`](active_projects.md) with:

```bash
uv run python scripts/generate_active_projects_doc.py
```

Default exemplar for paths: `projects/code_project/`.

## Infrastructure Modules

Current subpackages under `infrastructure/` (13):

- config
- core
- docker
- documentation
- llm
- project
- publishing
- rendering
- reporting
- scientific
- skills
- steganography
- validation

See `infrastructure/AGENTS.md` for module-specific function signatures and entry points.

## Test Status

```bash
uv run pytest tests/infra_tests/project/test_discovery.py -q
```

Result: 57 passed in ~0.22s (real data, no mocks).

Coverage gates (enforced in CI):

- infrastructure/ : >= 60%
- projects/*/src/ : >= 90% (matrix project tests; excludes `projects/fep_lean/tests/` — see below)
- `projects/fep_lean/src/` : >= 89% (dedicated CI job `fep_lean (gauss + lake)` when `projects/fep_lean/lean/lean-toolchain` exists)

Run full suite with:

```bash
uv run python scripts/01_run_tests.py --project code_project
```

### fep_lean (isolated project tree)

Run from `projects/fep_lean/` so `[tool.coverage.run] source = ["src"]` and multiprocessing coverage apply:

```bash
cd projects/fep_lean
uv run pytest tests/ --collect-only -q
uv run pytest tests/ -q --cov=src --cov-fail-under=89
```

Last collection: **285** tests across **28** modules (adds `tests/test_hermes_error_paths.py` — 9 `pytest-httpserver`-backed tests covering `HermesExplainer.preflight()` and `HermesConfig.fallback_models`). Parallelism: optional `FEP_LEAN_PREFETCH`, Stage 4 `ThreadPoolExecutor`, figure `ProcessPoolExecutor` (spawn; `FEP_LEAN_FIGURES_MP=0` forces serial); `pytest-xdist` and `pytest-httpserver` are dev dependencies. See `projects/fep_lean/tests/AGENTS.md` and `projects/fep_lean/docs/pipeline.md`.

**Hermes resilience (new):** `HermesConfig.fallback_models` is a first-class user-supplied OpenRouter chain (overrides `_FREE_MODEL_CHAIN`); `HermesExplainer.preflight()` runs one `max_tokens=1` probe at the start of Stage 4, flipping `cfg.enabled=False` on 4xx so credential failures surface in <10 s instead of ~12 min into the batch. Actionable 403 logs link to `https://openrouter.ai/settings/keys` and the Anthropic-direct fallback (`HERMES_API_BASE=https://api.anthropic.com/v1` + `ANTHROPIC_API_KEY`). See `projects/fep_lean/docs/troubleshooting.md#hermes-http-403--key-limit-exceeded`.

## Command Conventions

Use `uv run` for reproducibility:

- Tests: `uv run python scripts/01_run_tests.py --project <name>`
- Pipeline: `uv run python scripts/execute_pipeline.py --project <name> --core-only`
- Interactive: `./run.sh`
- Specific test: `uv run pytest path/to/test.py::test_name -q`

Avoid raw `python3` or `pytest` in documentation.

## Output Layout

- Working outputs: `projects/{name}/output/`
- Final deliverables: `output/{name}/` (subdirectories per project: pdf/, figures/, data/, reports/)
- No root-level `output/pdf/` or `output/project_combined.md`

## Core Patterns

**Thin orchestrator**:

Scripts in `scripts/` and `projects/{name}/scripts/` import computation from `infrastructure.*` or `projects.{name}.src.*`. They handle only I/O, orchestration, and reporting.

**No-mocks policy**: Tests use real computation, temp files (`tmp_path`), `pytest-httpserver` for HTTP, and `reportlab` for PDF tests.

**Reproducibility**: Fixed seeds, deterministic outputs, idempotent analysis scripts that skip if outputs exist.

## Pipeline Entry Points (from scripts/AGENTS.md)

See `scripts/AGENTS.md` for `PipelineStageDefinition` and `MENU_SCRIPT_MAPPING`.

Key signatures:

- `execute_test_pipeline(...)` in `infrastructure.reporting.pipeline_test_runner`
- `discover_projects(root: Path) -> list[Project]`

## Validation Commands

```bash
uv run python -m infrastructure.validation.cli markdown projects/{name}/manuscript/
uv run python -m infrastructure.validation.cli pdf output/{name}/pdf/
```

## Structure

```mermaid
flowchart TD
    Root[Root] --> Infra[infrastructure/ <br/>13 modules]
    Root --> Projects[projects/ <br/>see active_projects.md]
    Root --> Tests[tests/infra_tests/]
    Infra --> Core[core/ <br/>pipeline, logging, files, config]
    Projects --> Src[src/ <br/>project logic]
    Tests --> ProjectTests[project/test_*.py <br/>90% cov]
```

Link to this file from other documentation instead of repeating facts.

**Regeneration note:** Refresh [`active_projects.md`](active_projects.md) with `scripts/generate_active_projects_doc.py`. Update this file after meaningful CI or test-scale changes (fep_lean counts, new gates), using measured `pytest` output rather than estimates.
