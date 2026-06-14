"""Renderer for the generated ``docs/_generated/COUNTS.md`` factsheet.

This closes the last open doc-drift loop in the repo: ``COUNTS.md`` (formerly
the hand-maintained ``COUNTS.md``) is the only ``docs/_generated`` file
that historically had no generator, so ~40 commits chased its drift by hand.

The factsheet pins a small set of *volatile literals* that the codebase moves
underneath it:

- the tracked ``infrastructure/`` Python-file count (``git ls-files`` ∩ ``*.py``);
- the project-scope and publishing infrastructure ``pytest --collect-only`` totals;
- the public exemplar roster (from
  :func:`infrastructure.project.public_scope.public_project_names`);
- the importable ``infrastructure/`` package list.

These are all *derived from the live tree* by this module so ``--check`` can fail
when reality drifts from the committed doc. The matching gates live in
``tests/infra_tests/test_docs_discovery_consistency.py`` and parse the literals
back out via the markers ``Last refreshed count: **N**`` and
``Result: **N** project-scope ... **N** publishing tests``.

The per-exemplar test/coverage snapshot table is a *measured snapshot* rather
than a live derivation: running nine projects' coverage gates on every ``--check``
would be prohibitively slow and environment-fragile (each exemplar pins its own
``.venv`` and toolchain). The measured values live in :data:`EXEMPLAR_SNAPSHOT`
with an explicit measurement date; refresh them with ``--write`` after re-running
the per-project gates. The table's *membership* (one row per public exemplar) is
still gated against ``public_project_names`` by the consistency tests.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from infrastructure.project.public_scope import public_project_names

DOC_RELATIVE_PATH = Path("docs/_generated/COUNTS.md")

# Date the volatile-literal counts and module list were last refreshed (UTC).
GENERATED_DATE = "2026-06-13"

# Date the per-exemplar test/coverage snapshot table was last measured.
EXEMPLAR_SNAPSHOT_DATE = "2026-06-11"


@dataclass(frozen=True)
class ExemplarSnapshot:
    """One measured row of the exemplar test/coverage snapshot table."""

    name: str
    tests_collected: int
    coverage_pct: str  # rendered as-is, e.g. "96.96 %"


# Measured per-exemplar snapshot. ``tests_collected`` is the live
# ``pytest --collect-only`` total; ``coverage_pct`` is the latest per-project
# coverage gate (``--cov=projects/templates/<name>/src``). Refresh with --write
# after re-running the per-project gates; the rows are keyed by public-scope name
# so the consistency test gates membership, not the numbers.
EXEMPLAR_SNAPSHOT: tuple[ExemplarSnapshot, ...] = (
    # template_active_inference coverage is preserved from the prior measurement
    # (2026-06-05): its project-local .venv pins a numpy/Python ABI that cannot be
    # exercised from the repo-root interpreter, so the gate is re-derived in its
    # own environment, not here. The collected-test count is from --collect-only.
    ExemplarSnapshot("template_active_inference", 382, "91.35 %"),
    ExemplarSnapshot("template_autoresearch_project", 220, "92.81 %"),
    ExemplarSnapshot("template_autoscientists", 87, "99.60 %"),
    ExemplarSnapshot("template_code_project", 197, "96.96 %"),
    ExemplarSnapshot("template_newspaper", 53, "94.37 %"),
    ExemplarSnapshot("template_prose_project", 78, "100.00 %"),
    ExemplarSnapshot("template_sia", 40, "97.16 %"),
    ExemplarSnapshot("template_template", 89, "91.62 %"),
    ExemplarSnapshot("template_textbook", 112, "96.73 %"),
)


def tracked_infra_python_count(repo_root: Path) -> int:
    """Count git-tracked ``infrastructure/`` Python files (matches the gate)."""
    tracked = subprocess.run(  # noqa: S603 - fixed argv, repo-local git
        ["git", "ls-files", "infrastructure"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    return sum(1 for path in tracked if path.endswith(".py"))


def _collected_count(repo_root: Path, rel_path: str) -> int:
    """Return the ``pytest --collect-only`` total for ``rel_path``."""
    proc = subprocess.run(  # noqa: S603 - fixed argv, repo-local pytest
        [sys.executable, "-m", "pytest", rel_path, "--collect-only", "-q", "--no-cov"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    match = re.search(r"(?P<count>\d+) tests? collected", proc.stdout)
    if not match:
        raise RuntimeError(f"could not parse collected count for {rel_path}:\n{proc.stdout}")
    return int(match.group("count"))


def project_test_count(repo_root: Path) -> int:
    """Project-scope infrastructure test collection total."""
    return _collected_count(repo_root, "tests/infra_tests/project/")


def publishing_test_count(repo_root: Path) -> int:
    """Publishing infrastructure test collection total."""
    return _collected_count(repo_root, "tests/infra_tests/publishing/")


def infrastructure_packages(repo_root: Path) -> list[str]:
    """Importable (``__init__.py``-bearing) ``infrastructure/`` subpackages."""
    infra = repo_root / "infrastructure"
    return sorted(p.parent.name for p in infra.glob("*/__init__.py") if not p.parent.name.startswith("_"))


@dataclass(frozen=True)
class CountsFacts:
    """The volatile literals derived from the live tree for COUNTS.md."""

    public_projects: list[str]
    packages: list[str]
    infra_py_count: int
    project_tests: int
    publishing_tests: int


def collect_facts(repo_root: Path) -> CountsFacts:
    """Derive every volatile literal COUNTS.md pins from the live tree."""
    return CountsFacts(
        public_projects=[name.split("/")[-1] for name in public_project_names(repo_root)],
        packages=infrastructure_packages(repo_root),
        infra_py_count=tracked_infra_python_count(repo_root),
        project_tests=project_test_count(repo_root),
        publishing_tests=publishing_test_count(repo_root),
    )


def _roster_block(names: list[str]) -> str:
    return "\n".join(f"- `{name}`" for name in names)


def _packages_block(packages: list[str]) -> str:
    return "\n".join(f"- {pkg}" for pkg in packages)


def _exemplar_table() -> str:
    rows = [
        "| Project | Tests collected | `src/` line+branch coverage |",
        "|---------|-----------------|----------------------------|",
    ]
    for row in EXEMPLAR_SNAPSHOT:
        rows.append(f"| `{row.name}` | {row.tests_collected} | {row.coverage_pct} |")
    return "\n".join(rows)


def render_counts_doc(facts: CountsFacts) -> str:
    """Render the full COUNTS.md content from derived facts + measured snapshot."""
    roster = _roster_block(facts.public_projects)
    packages = _packages_block(facts.packages)
    n_pkgs = len(facts.packages)
    return f"""# Canonical Factsheet

> Auto-generated by `scripts/generate_counts.py` from live repo state. Do not edit
> manually — run `uv run python scripts/generate_counts.py --write` to refresh.

**Generated from live repo state on {GENERATED_DATE} (UTC).** Volatile literals are \
re-derived on every run: tracked `infrastructure/` Python-file count via \
`git ls-files infrastructure | grep .py` (**{facts.infra_py_count}**), \
project-scope + publishing test collection via `pytest --collect-only` \
(**{facts.project_tests}** / **{facts.publishing_tests}**), the public exemplar \
roster, and the importable module list. The per-exemplar test/coverage snapshot \
table is a measured snapshot (see Test Status).

This file aggregates verifiable facts from discovery scripts, CI configuration, and test execution. Human-written documentation should link here rather than duplicate lists or numbers.

## Project Roster

**Always-present canonical exemplars** (the public exemplar projects guaranteed to live under `projects/`):

{roster}

Optional add-on: `projects/archive/template_search_project` (mirrored read-only from the private repo's `archive/`) can be copied under `projects/active/` for literature-search workflows.

Private lifecycle projects live outside this public repo in a separate external repository (location set via `TEMPLATE_PRIVATE_PROJECTS_ROOT` or `.private_projects_root`). The simplified sidecar defaults to `working/` and `archive/`; optional legacy `active/`, `published/`, and `other/` folders are still recognized when present. `run.sh`/`infrastructure.orchestration` symlinks existing private lifecycle folders into same-named typed subfolders under `template/projects/` (`working/*` → `projects/working/*`, `archive/*` → `projects/archive/*`, optional `active/*` → `projects/active/*`, …) before discovery/rendering; only `projects/templates/` and optional `projects/active/` are default-rendered, while `working/` and `archive/` are non-rendered mirrors for explicit targeted work. Override with `TEMPLATE_PRIVATE_PROJECTS_ROOT` or `.private_projects_root`; disable auto-sync with `TEMPLATE_SKIP_LINK_SYNC=1`; inspect with `uv run python -m infrastructure.orchestration link-projects --dry-run`.

**Public CI/documentation project scope** (`projects/`, filtered through `infrastructure.project.public_scope`; authoritative snapshot → [`active_projects.md`](active_projects.md)):

{roster}

`projects/_test_project/` is a stub layout used by validation tests only — omitted from `discover_projects()` (path may be absent in sparse checkouts; not a tracked exemplar tree).

**Work-in-progress projects** (`projects/working/`, not discovered/rendered): local-only symlinks to the private repo's `working/` projects — roster omitted from public docs; list with `ls projects/working/`.

**Archived projects** (`projects/archive/`, preserved but not executed): local-only symlinks to the private repo's `archive/` projects (roster omitted from public docs) — list with `ls projects/archive/`. `projects/published/` and `projects/other/` are optional legacy non-rendered lifecycle mirrors.

Regenerate [`active_projects.md`](active_projects.md) with:

```bash
uv run python scripts/generate_active_projects_doc.py
```

Default exemplar for paths: `projects/templates/template_code_project/`.

## Infrastructure Modules

Current importable Python subpackages under `infrastructure/` ({n_pkgs}):

{packages}

Plus `infrastructure/config/`, `infrastructure/docker/`, and `infrastructure/logrotate.d/` (configuration/documentation directories, not Python packages). Recount with:

```bash
find infrastructure -mindepth 1 -maxdepth 1 -type d -name '[!.]*' \\
  -exec sh -c 'test -f "$1/__init__.py" && basename "$1"' sh {{}} \\; | wc -l
```

Tracked Python modules (matches the drift gate):

```bash
git ls-files infrastructure | grep -c '\\.py$'
```

(Last refreshed count: **{facts.infra_py_count}** on {GENERATED_DATE} UTC — point-in-time; re-derive with the command above, the literal drifts as the tree changes.)

See `infrastructure/AGENTS.md` for module-specific function signatures and entry points.

## Test Status

```bash
uv run pytest tests/infra_tests/project/test_discovery.py -q
```

Current collection commands:

```bash
uv run pytest tests/infra_tests/project/ --collect-only -q --no-cov
uv run pytest tests/infra_tests/publishing/ --collect-only -q --no-cov
```

Result: **{facts.project_tests}** project-scope infrastructure tests collected and **{facts.publishing_tests}** publishing tests collected. Full behavioral gates still live in CI and in the verification commands listed by the relevant `AGENTS.md` files.

**Exemplar `pytest --collect-only` totals** (measured {EXEMPLAR_SNAPSHOT_DATE}; `template_active_inference` coverage preserved from its 2026-06-05 project-local gate run — see note below):

{_exemplar_table()}

Collection counts come from per-project `uv run pytest tests/ --collect-only -q --no-cov` runs; coverage values come from the latest per-project coverage gates (`uv run pytest projects/templates/<name>/tests/ --cov=projects/templates/<name>/src`). Re-run the per-project coverage command after changing project `src/` or tests, then refresh this snapshot with `uv run python scripts/generate_counts.py --write`. `template_active_inference` pins its own `.venv`/toolchain, so its coverage is re-derived in that environment, not from the repo-root interpreter. Orchestration modules (`analysis.py`, `figures.py`, `dashboard.py`, `manuscript_variables.py`) are in the coverage denominator for the code exemplar; `experiment_config.py` is the shared loader for `manuscript/config.yaml` → `experiment:`.

Drift-checker coverage: `uv run python scripts/check_template_drift.py --strict`. Repo `scripts/` fat files emit **WARNING**; project `scripts/` fat files emit **ERROR** through the thin-orchestrator detectors. Per-exemplar detectors include function name drift, test class drift, `__all__` doc drift, coverage floor drift, dead links, oversize `src/*.py`, blanket `except Exception`, mocks in tests, and canonical-file presence.

**Thin-orchestrator gates:**

| Gate | Command | Threshold |
| --- | --- | --- |
| Exemplar drift | `uv run python scripts/check_template_drift.py --strict` | 9+2 detectors |
| Module line count | `uv run python scripts/gates/module_line_count_check.py` | warn ≥800 / fail ≥950 (`infrastructure/`, `scripts/`); warn ≥150 / fail ≥250 (`projects/{{exemplar}}/scripts/` via `PUBLIC_PROJECT_NAMES`) |
| Unified health | `uv run python -m infrastructure.core.health` | optional `--gates=module-line-count` |
| Tracked projects | `uv run python scripts/check_tracked_projects.py` | non-exemplar paths under `projects/` |
| Generated artifacts | `uv run python scripts/check_tracked_generated_artifacts.py` | disposable `output/` trees |

Coverage gates (enforced in CI):

- infrastructure/ : >= 60% (measured baseline → [`docs/development/coverage-gaps.md`](../development/coverage-gaps.md))
- public template project `src/` trees : >= 90% (matrix project tests; public lint/type paths come from `uv run python -m infrastructure.project.public_scope source-paths`)

Run full suite with:

```bash
uv run python scripts/01_run_tests.py --project template_code_project
```

## Command Conventions

Use `uv run` for reproducibility:

- Tests: `uv run python scripts/01_run_tests.py --project <name>`
- Pipeline: `uv run python scripts/execute_pipeline.py --project <name> --core-only`
- Interactive: `./run.sh`
- Specific test: `uv run pytest path/to/test.py::test_name -q`

Avoid raw `python3` or `pytest` in documentation.

## Output Layout

- Working outputs: `projects/{{name}}/output/`
- Final deliverables: `output/{{name}}/` (subdirectories per project: pdf/, figures/, data/, reports/)
- No root-level `output/pdf/` or `output/project_combined.md`

## Core Patterns

**Thin orchestrator**:

Scripts in `scripts/` and `projects/{{name}}/scripts/` import computation from `infrastructure.*` or `projects.{{name}}.src.*`. They handle only I/O, orchestration, and reporting.

**`template_code_project/src/` layout:**
- `optimizer.py`, `invariants.py` — math primitives, infrastructure-free
- `experiment_config.py` — `load_experiment_config()`; single parser for `manuscript/config.yaml` → `experiment:`
- `analysis.py` — experiment orchestration, stability/benchmark, validation, publishing, `main()`
- `figures.py` — matplotlib figure generators (uses `load_experiment_config`)
- `dashboard.py` — Plotly dashboard payload + HTML (`load_experiment_config`)
- `manuscript_variables.py` — `{{{{TOKEN}}}}` substitution (`load_experiment_config`, `quadratic_optimum`)

**No-mocks policy**: Tests use real computation, temp files (`tmp_path`), `pytest-httpserver` for HTTP, and `reportlab` for PDF tests.

**Reproducibility**: Fixed seeds, deterministic outputs, idempotent analysis scripts that skip if outputs exist.

## Pipeline Entry Points (from scripts/AGENTS.md)

See `scripts/AGENTS.md` for the pipeline entry-point inventory. The interactive menu's single source of truth is `infrastructure.orchestration.menu.MENU_OPTIONS`.

Key signatures:

- `execute_test_pipeline(...)` in `infrastructure.reporting.pipeline_test_runner`
- `discover_projects(root: Path) -> list[Project]`

## Validation Commands

```bash
uv run python -m infrastructure.validation.cli markdown projects/{{name}}/manuscript/
uv run python -m infrastructure.validation.cli pdf output/{{name}}/pdf/
```

## Structure

```mermaid
flowchart TD
    Root[Root] --> Infra[infrastructure/ <br/>{n_pkgs} importable packages]
    Root --> Projects[projects/ <br/>see active_projects.md]
    Root --> Tests[tests/infra_tests/]
    Infra --> Core[core/ <br/>pipeline, logging, files, config]
    Projects --> Src[src/ <br/>project logic]
    Tests --> ProjectTests[project/test_*.py <br/>90% cov]
```

Link to this file from other documentation instead of repeating facts.

**Regeneration note:** Refresh [`active_projects.md`](active_projects.md) with `scripts/generate_active_projects_doc.py`. Re-derive this file with `uv run python scripts/generate_counts.py --write` after meaningful CI or test-scale changes. Re-run `uv run python scripts/check_template_drift.py --strict` and `uv run python scripts/gates/module_line_count_check.py` when drift or line-count gates change.
"""


def write_counts_doc(repo_root: Path, out_path: Path | None = None) -> Path:
    """Render and write COUNTS.md; returns the written path."""
    target = out_path if out_path is not None else repo_root / DOC_RELATIVE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_counts_doc(collect_facts(repo_root)), encoding="utf-8")
    return target


def check_counts_doc(repo_root: Path) -> tuple[bool, str]:
    """Return (in_sync, message) comparing on-disk COUNTS.md with a fresh render."""
    doc_path = repo_root / DOC_RELATIVE_PATH
    rendered = render_counts_doc(collect_facts(repo_root))
    on_disk = doc_path.read_text(encoding="utf-8") if doc_path.is_file() else ""
    if rendered == on_disk:
        return True, "COUNTS.md: OK (in sync with live tree)"
    return False, f"STALE: {DOC_RELATIVE_PATH} differs from a fresh render — run --write"
