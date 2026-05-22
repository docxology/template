# Canonical Factsheet

**Generated from live repo state on 2026-05-22 (UTC).** Last measured runs: `generate_active_projects_doc.py`, `generate_architecture_overview.py`, `pytest tests/infra_tests/project/test_discovery.py tests/infra_tests/test_docs_discovery_consistency.py -q` (**60** passed), `pytest tests/infra_tests/project/test_linking.py tests/infra_tests/core/test_pipeline_control_extensions.py -q` (**56** passed), `pytest projects/*/tests/ --collect-only` per exemplar below, `find infrastructure -name '*.py' -type f | wc -l` (**365** `.py` files, point-in-time; this count drifts as the tree changes, always re-derive with the command rather than trusting the literal). Counts below for `fep_lean` are historical from archived/restored trees (see commands).

This file aggregates verifiable facts from discovery scripts, CI configuration, and test execution. Human-written documentation should link here rather than duplicate lists or numbers.

## Project Roster

**Always-present canonical exemplars** (the only two guaranteed to live under `projects/`):

- `template_code_project`
- `template_prose_project`

Optional add-on: `projects_archive/template_search_project` can be restored under `projects/` for literature-search workflows.

Private active projects live outside this public repo at `/Users/4d/Documents/GitHub/projects/active/` by default and are symlinked into `template/projects/` by `run.sh`/`infrastructure.orchestration` before discovery. Override with `TEMPLATE_PRIVATE_PROJECTS_ROOT` or `.private_projects_root`; disable auto-sync with `TEMPLATE_SKIP_LINK_SYNC=1`; inspect with `uv run python -m infrastructure.orchestration link-projects --dry-run`.

**Public CI/documentation project scope** (`projects/`, filtered through `infrastructure.project.public_scope`; authoritative snapshot → [`active_projects.md`](active_projects.md)):

- `template_code_project`
- `template_prose_project`

`projects/_test_project/` is a stub layout used by validation tests only — omitted from `discover_projects()` (path may be absent in sparse checkouts; not a tracked exemplar tree).

**In-progress projects** (`projects_in_progress/`, not discovered until moved under `projects/`): local-only roster omitted from public docs; inspect the directory in a local checkout when needed.

**Archived projects** (`projects_archive/`, preserved but not executed): includes `fep_lean`, `act_inf_metaanalysis`, `cognitive_integrity`, and others — list with `ls projects_archive/`.

Regenerate [`active_projects.md`](active_projects.md) with:

```bash
uv run python scripts/generate_active_projects_doc.py
```

Default exemplar for paths: `projects/template_code_project/`.

## Infrastructure Modules

Current importable Python subpackages under `infrastructure/` (17):

- benchmark
- core
- doctor
- documentation
- llm
- orchestration
- project
- prose
- publishing
- reference
- rendering
- reporting
- scientific
- search
- skills
- steganography
- validation

Plus `infrastructure/config/`, `infrastructure/docker/`, and `infrastructure/logrotate.d/` (configuration/documentation directories, not Python packages). Recount with:

```bash
find infrastructure -mindepth 1 -maxdepth 1 -type d -name '[!.]*' \
  -exec sh -c 'test -f "$1/__init__.py" && basename "$1"' sh {} \; | wc -l
```

Python modules on disk:

```bash
find infrastructure -name '*.py' -type f | wc -l
```

(Last refreshed count: **365** on 2026-05-22 UTC — point-in-time; re-derive with the command above, the literal drifts as the tree changes.)

See `infrastructure/AGENTS.md` for module-specific function signatures and entry points.

## Test Status

```bash
uv run pytest tests/infra_tests/project/test_discovery.py -q
```

Current discovery/docs command:

```bash
uv run pytest tests/infra_tests/project/test_discovery.py tests/infra_tests/test_docs_discovery_consistency.py -q
```

Result: 60 passed in ~0.63s (real data, no mocks). Link-sync and pipeline-control command:

```bash
uv run pytest tests/infra_tests/project/test_linking.py tests/infra_tests/core/test_pipeline_control_extensions.py -q
```

Result: 56 passed in ~0.76s (real symlinks and file-backed HITL state, no mocks).

**Exemplar `pytest --collect-only` totals** (2026-05-19):

| Project | Tests collected | `src/` line+branch coverage |
|---------|-----------------|----------------------------|
| `template_code_project` | 117 | 99.52 % |
| `template_prose_project` | 76 | 100.00 % |

The prose count grew from 67 → 76 during the May 2026 hardening pass: eight new `tests/test_config.py` cases that exercise the strict-key validator + `__post_init__` invariants in `src/config.py`, plus one new `tests/test_scripts.py::test_z_generate_manuscript_variables` subprocess test.

Drift-checker self-tests (separate suite at `tests/infra_tests/test_check_template_drift.py`): **20 passed**, gating the nine detectors that run against both exemplars (function name drift, test class drift, `__all__` doc drift, coverage floor drift, dead link, oversize `src/*.py`, blanket `except Exception`, mocks in tests, canonical-file presence).

Coverage gates (enforced in CI):

- infrastructure/ : >= 60%
- public template project `src/` trees : >= 90% (matrix project tests; public lint/type paths come from `uv run python -m infrastructure.project.public_scope source-paths`)
- `projects/fep_lean/src/` : >= 89% (dedicated CI job `fep_lean (gauss + lake)` when `projects/fep_lean/lean/lean-toolchain` exists)

Run full suite with:

```bash
uv run python scripts/01_run_tests.py --project template_code_project
```

### fep_lean (archived — `projects_archive/fep_lean/`)

`fep_lean` is currently archived and not executed by the active pipeline. When present under `projects/`, it has its own coverage gate (≥89 %) and isolated `pyproject.toml`. Historical run from the archive tree:

```bash
cd projects_archive/fep_lean
uv run pytest tests/ --collect-only -q
uv run pytest tests/ -q --cov=src --cov-fail-under=89
```

Last historical collection: **285** tests across **28** modules (adds `tests/test_hermes_error_paths.py` — 9 `pytest-httpserver`-backed tests covering `HermesExplainer.preflight()` and `HermesConfig.fallback_models`). Parallelism: optional `FEP_LEAN_PREFETCH`, Stage 4 `ThreadPoolExecutor`, figure `ProcessPoolExecutor` (spawn; `FEP_LEAN_FIGURES_MP=0` forces serial); `pytest-xdist` and `pytest-httpserver` are dev dependencies. See `projects_archive/fep_lean/tests/AGENTS.md` and `projects_archive/fep_lean/docs/pipeline.md`.

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

**`template_code_project/src/` layout (post-May-2026 split):**
- `optimizer.py`, `invariants.py` — math primitives, infrastructure-free
- `analysis.py` — orchestration (experiments + dashboard + validation + publishing + `main()`); re-exports figure generators from `figures.py` for back-compat
- `figures.py` — the six `generate_*` plot/visualization functions + `apply_visualization_style` + `VIZ_CONFIG` + `_agency_category` + `_save_figure_data` + `_load_experiment_config`
- `dashboard.py` — `scripts/build_dashboard.py` orchestration
- `manuscript_variables.py` — `{{TOKEN}}` substitution generator

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
    Root[Root] --> Infra[infrastructure/ <br/>17 importable packages]
    Root --> Projects[projects/ <br/>see active_projects.md]
    Root --> Tests[tests/infra_tests/]
    Infra --> Core[core/ <br/>pipeline, logging, files, config]
    Projects --> Src[src/ <br/>project logic]
    Tests --> ProjectTests[project/test_*.py <br/>90% cov]
```

Link to this file from other documentation instead of repeating facts.

**Regeneration note:** Refresh [`active_projects.md`](active_projects.md) with `scripts/generate_active_projects_doc.py`. Update this file after meaningful CI or test-scale changes (fep_lean counts, new gates), using measured `pytest` output rather than estimates.
