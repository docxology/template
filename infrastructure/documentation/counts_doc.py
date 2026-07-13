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

Per-exemplar collection totals are derived live with ``pytest --collect-only``.
Coverage remains a separately labelled measured snapshot because recomputing all
23 coverage gates during every documentation check would be prohibitively slow.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import os
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.project_pyproject import project_declares_dev_extra
from infrastructure.project.public_scope import public_project_names

DOC_RELATIVE_PATH = Path("docs/_generated/COUNTS.md")
COVERAGE_PROVENANCE_RELATIVE_PATH = Path("docs/_generated/coverage_snapshot.json")
COVERAGE_PROVENANCE_SCHEMA_VERSION = 2

# Date the volatile-literal counts and module list were last refreshed (UTC).
GENERATED_DATE = "2026-07-13"

# Date the per-exemplar test/coverage snapshot table was last measured.
EXEMPLAR_SNAPSHOT_DATE = "2026-07-11"


@dataclass(frozen=True)
class ExemplarSnapshot:
    """One measured coverage row; collection count is always derived live."""

    name: str
    coverage_pct: str  # rendered as-is, e.g. "96.96 %"


# Measured per-exemplar coverage snapshot. Collection totals are intentionally
# absent here and are derived in isolated project environments on every run.
EXEMPLAR_SNAPSHOT: tuple[ExemplarSnapshot, ...] = (
    # template_active_inference coverage is re-derived in its OWN environment
    # (its project-local .venv pins a numpy/Python ABI the repo-root interpreter
    # cannot exercise): measured 2026-07-11 via
    # `stage_01_test.py --project templates/template_active_inference
    # --project-only --include-slow` (699 passed). Collected count from
    # --collect-only in the project env.
    ExemplarSnapshot("template_active_inference", "93.55 %"),
    ExemplarSnapshot("template_autopoiesis", "96.41 %"),
    ExemplarSnapshot("template_autoresearch_project", "92.81 %"),
    ExemplarSnapshot("template_autoscientists", "99.60 %"),
    ExemplarSnapshot("template_code_project", "98.78 %"),
    ExemplarSnapshot("template_data_descriptor", "99.13 %"),
    ExemplarSnapshot("template_eda_notebook", "100.00 %"),
    ExemplarSnapshot("template_formal", "96.03 %"),
    ExemplarSnapshot("template_gold_refinement", "97.55 %"),
    ExemplarSnapshot("template_literature_meta_analysis", "96.77 %"),
    ExemplarSnapshot("template_madlib", "93.96 %"),
    ExemplarSnapshot("template_methods_paper", "99.01 %"),
    ExemplarSnapshot("template_newspaper", "99.81 %"),
    ExemplarSnapshot("template_pitch_deck", "97.70 %"),
    ExemplarSnapshot("template_pools_rules_tools", "95.52 %"),
    ExemplarSnapshot("template_prose_project", "100.00 %"),
    # Union of two independent 2026-07-10 coverage-debt closures (both real
    # no-mock suites over visuals.py, written in parallel sessions): 95 tests,
    # 99.05 % — was 55.91 % when the 1500-line kmyth/TPM module landed with 7.
    ExemplarSnapshot("template_redacted_report", "98.83 %"),
    ExemplarSnapshot("template_registered_report", "96.37 %"),
    ExemplarSnapshot("template_search_project", "95.13 %"),
    ExemplarSnapshot("template_sia", "97.16 %"),
    ExemplarSnapshot("template_storybook", "93.92 %"),
    ExemplarSnapshot("template_template", "99.37 %"),
    ExemplarSnapshot("template_textbook", "96.73 %"),
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


def _exemplar_collected_count(repo_root: Path, name: str) -> int:
    """Collect an exemplar in its own declared environment."""
    project_root = repo_root / "projects" / "templates" / name
    uv = shutil.which("uv")
    if uv is None:
        raise RuntimeError("uv is required to derive isolated exemplar collection totals")
    environment = dict(os.environ)
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        f"{repo_root}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else str(repo_root)
    )
    command = [uv, "run", "--project", str(project_root)]
    if project_declares_dev_extra(project_root):
        command.extend(["--extra", "dev"])
    command.extend(["pytest", "tests/", "--collect-only", "-q", "--no-cov"])
    proc = subprocess.run(  # noqa: S603 - resolved uv executable, fixed arguments
        command,
        cwd=project_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"could not collect exemplar {name} (exit {proc.returncode}):\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    match = re.search(r"(?P<count>\d+) tests? collected", proc.stdout)
    if not match:
        raise RuntimeError(f"could not parse collected count for {name}:\n{proc.stdout}")
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
    exemplar_tests: dict[str, int]


def collect_facts(repo_root: Path) -> CountsFacts:
    """Derive every volatile literal COUNTS.md pins from the live tree."""
    public_projects = [name.split("/")[-1] for name in public_project_names(repo_root)]
    return CountsFacts(
        public_projects=public_projects,
        packages=infrastructure_packages(repo_root),
        infra_py_count=tracked_infra_python_count(repo_root),
        project_tests=project_test_count(repo_root),
        publishing_tests=publishing_test_count(repo_root),
        exemplar_tests={name: _exemplar_collected_count(repo_root, name) for name in public_projects},
    )


def _roster_block(names: list[str]) -> str:
    return "\n".join(f"- `{name}`" for name in names)


def _packages_block(packages: list[str]) -> str:
    return "\n".join(f"- {pkg}" for pkg in packages)


def _exemplar_table(exemplar_tests: dict[str, int]) -> str:
    rows = [
        "| Project | Tests collected | `src/` line+branch coverage |",
        "|---------|-----------------|----------------------------|",
    ]
    for row in EXEMPLAR_SNAPSHOT:
        if row.name in exemplar_tests:
            rows.append(f"| `{row.name}` | {exemplar_tests[row.name]} | {row.coverage_pct} |")
    return "\n".join(rows)


def exemplar_source_hash(repo_root: Path, name: str) -> str:
    """Hash tracked source and tests that determine one exemplar's coverage."""
    project_root = repo_root / "projects" / "templates" / name
    digest = hashlib.sha256()
    relative_roots = [(project_root / root_name).relative_to(repo_root).as_posix() for root_name in ("src", "tests")]
    tracked = subprocess.run(  # noqa: S603 - fixed git command and paths
        ["git", "ls-files", "--", *relative_roots],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if tracked.returncode == 0:
        files = sorted(repo_root / relative for relative in tracked.stdout.splitlines())
    else:
        # Unit callers may supply a temporary non-Git tree. Production
        # repositories always take the tracked-file branch above so ignored
        # build metadata cannot contaminate cross-platform provenance.
        files = sorted(
            path
            for root_name in ("src", "tests")
            for path in (project_root / root_name).rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        )
    for path in files:
        digest.update(path.relative_to(project_root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def build_coverage_provenance(repo_root: Path) -> dict[str, object]:
    """Build provenance for the checked-in coverage percentages."""
    source_commit = subprocess.run(  # noqa: S603 - fixed git command
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return {
        "schema_version": COVERAGE_PROVENANCE_SCHEMA_VERSION,
        "measured_at": EXEMPLAR_SNAPSHOT_DATE,
        "source_commit": source_commit,
        "projects": {
            row.name: {
                "coverage_pct": row.coverage_pct,
                "source_hash": exemplar_source_hash(repo_root, row.name),
            }
            for row in EXEMPLAR_SNAPSHOT
        },
    }


def write_coverage_provenance(repo_root: Path) -> Path:
    """Write coverage source provenance after coverage gates have run."""
    target = repo_root / COVERAGE_PROVENANCE_RELATIVE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(build_coverage_provenance(repo_root), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def validate_coverage_provenance(repo_root: Path) -> None:
    """Fail closed when a coverage percentage is stale for its source tree."""
    path = repo_root / COVERAGE_PROVENANCE_RELATIVE_PATH
    if not path.is_file():
        raise RuntimeError(f"missing coverage provenance: {COVERAGE_PROVENANCE_RELATIVE_PATH}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("coverage provenance root must be a mapping")
    if payload.get("schema_version") != COVERAGE_PROVENANCE_SCHEMA_VERSION:
        raise RuntimeError(f"coverage provenance schema mismatch: expected {COVERAGE_PROVENANCE_SCHEMA_VERSION}")
    projects = payload.get("projects")
    if not isinstance(projects, dict):
        raise RuntimeError("coverage provenance has no projects mapping")
    expected_names = {row.name for row in EXEMPLAR_SNAPSHOT}
    if set(projects) != expected_names:
        raise RuntimeError("coverage provenance project roster does not match the public snapshot")
    for row in EXEMPLAR_SNAPSHOT:
        record = projects.get(row.name)
        if not isinstance(record, dict) or record.get("coverage_pct") != row.coverage_pct:
            raise RuntimeError(f"coverage provenance percentage mismatch: {row.name}")
        if record.get("source_hash") != exemplar_source_hash(repo_root, row.name):
            raise RuntimeError(
                f"stale coverage snapshot for {row.name}: source hash changed; "
                "rerun its coverage gate, then refresh coverage provenance"
            )


def render_counts_doc(facts: CountsFacts) -> str:
    """Render the full COUNTS.md content from derived facts + measured snapshot."""
    roster = _roster_block(facts.public_projects)
    packages = _packages_block(facts.packages)
    n_pkgs = len(facts.packages)
    return f"""# Canonical Factsheet

> Auto-generated by `scripts/docgen/counts.py` from live repo state. Do not edit
> manually — run `uv run python scripts/docgen/counts.py --write` to refresh.

**Generated from live repo state on {GENERATED_DATE} (UTC).** Volatile literals are \
re-derived on every run: tracked `infrastructure/` Python-file count via \
`git ls-files infrastructure | grep .py` (**{facts.infra_py_count}**), \
project-scope + publishing test collection via `pytest --collect-only` \
(**{facts.project_tests}** / **{facts.publishing_tests}**), the public exemplar \
roster, and the importable module list. The per-exemplar test/coverage snapshot \
table is a measured snapshot with source-commit and source-hash provenance in
[`coverage_snapshot.json`](coverage_snapshot.json) (see Test Status).

This file aggregates verifiable facts from discovery scripts, CI configuration, and test execution. Human-written documentation should link here rather than duplicate lists or numbers.

## Project Roster

Private lifecycle projects live outside this public repo in a separate external repository (location set via `TEMPLATE_PRIVATE_PROJECTS_ROOT` or `.private_projects_root`). The simplified sidecar defaults to `working/` and `archive/`; optional `ongoing/` (long-lived projects with no publication target) plus legacy `active/`, `published/`, and `other/` folders are still recognized when present. `run.sh`/`infrastructure.orchestration` symlinks existing private lifecycle folders into same-named typed subfolders under `template/projects/` (`working/*` → `projects/working/*`, `ongoing/*` → `projects/ongoing/*`, `archive/*` → `projects/archive/*`, optional `active/*` → `projects/active/*`, …) before discovery/rendering; only `projects/templates/` and optional `projects/active/` are default-rendered, while `working/`, `ongoing/`, and `archive/` are non-rendered mirrors for explicit targeted work. Override with `TEMPLATE_PRIVATE_PROJECTS_ROOT` or `.private_projects_root`; disable auto-sync with `TEMPLATE_SKIP_LINK_SYNC=1`; inspect with `uv run python -m infrastructure.orchestration link-projects --dry-run`.

**Public CI/documentation project scope** (`projects/`, filtered through `infrastructure.project.public_scope`; authoritative snapshot → [`active_projects.md`](active_projects.md)):

{roster}

`projects/_test_project/` is a stub layout used by validation tests only — omitted from `discover_projects()` (path may be absent in sparse checkouts; not a tracked exemplar tree).

**Work-in-progress projects** (`projects/working/`, not discovered/rendered): local-only symlinks to the private repo's `working/` projects — roster omitted from public docs; list with `ls projects/working/`.

**Ongoing projects** (`projects/ongoing/`, not discovered/rendered): local-only symlinks to the private repo's `ongoing/` projects — long-lived work with no publication target, roster omitted from public docs; render explicitly via the qualified name `ongoing/<name>`; list with `ls projects/ongoing/`.

**Archived projects** (`projects/archive/`, preserved but not executed): local-only symlinks to the private repo's `archive/` projects (roster omitted from public docs) — list with `ls projects/archive/`. `projects/published/` and `projects/other/` are optional legacy non-rendered lifecycle mirrors.

Regenerate [`active_projects.md`](active_projects.md) with:

```bash
uv run python scripts/docgen/active_projects.py
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

**Exemplar `pytest --collect-only` totals** (derived live in each project's declared environment; coverage snapshot last updated {EXEMPLAR_SNAPSHOT_DATE}; `template_active_inference` coverage preserved from its 2026-06-05 project-local gate run — see note below):

{_exemplar_table(facts.exemplar_tests)}

Collection counts come from per-project `uv run pytest tests/ --collect-only -q --no-cov` runs; coverage values come from the latest per-project coverage gates (`uv run pytest projects/templates/<name>/tests/ --cov=projects/templates/<name>/src`). After changing project `src/` or tests, rerun that project's coverage gate and then explicitly refresh provenance with `uv run python scripts/docgen/counts.py --refresh-coverage-provenance --write`; ordinary `--write` fails when source hashes no longer match. `template_active_inference` pins its own `.venv`/toolchain, so its coverage is re-derived in that environment, not from the repo-root interpreter. Orchestration modules (`analysis.py`, `figures.py`, `dashboard.py`, `manuscript_variables.py`) are in the coverage denominator for the code exemplar; `experiment_config.py` is the shared loader for `manuscript/config.yaml` → `experiment:`.

Drift-checker coverage: `uv run python scripts/audit/check_template_drift.py --strict`. Repo `scripts/` fat files emit **WARNING**; project `scripts/` fat files emit **ERROR** through the thin-orchestrator detectors. Per-exemplar detectors include function name drift, test class drift, `__all__` doc drift, coverage floor drift, dead links, oversize `src/*.py`, blanket `except Exception`, mocks in tests, and canonical-file presence.

**Thin-orchestrator gates:**

| Gate | Command | Threshold |
| --- | --- | --- |
| Exemplar drift | `uv run python scripts/audit/check_template_drift.py --strict` | 9+2 detectors |
| Module line count | `uv run python scripts/gates/module_line_count_check.py` | warn ≥800 / fail ≥950 (`infrastructure/`, `scripts/`); warn ≥150 / fail ≥250 (`projects/{{exemplar}}/scripts/` via `PUBLIC_PROJECT_NAMES`) |
| Unified health | `uv run python -m infrastructure.core.health` | optional `--gates=module-line-count` |
| Tracked public scope | `uv run python scripts/audit/check_tracked_all.py` | non-template paths under `projects/`, `fonds/`, `rules/`, and `tools/` |
| Generated artifacts | `uv run python scripts/audit/check_tracked_generated_artifacts.py` | prohibited generated state outside the canonical public-output allowlist |

Coverage gates (enforced in CI):

- infrastructure/ : >= 60% (measured baseline → [`docs/development/coverage-gaps.md`](../development/coverage-gaps.md))
- public template project `src/` trees : >= 90% (matrix project tests; Ruff uses `public_scope lint-paths`, while mypy uses the import-safe `source-paths`)

Run full suite with:

```bash
uv run python scripts/pipeline/stage_01_test.py --project template_code_project
```

## Command Conventions

Use `uv run` for reproducibility:

- Tests: `uv run python scripts/pipeline/stage_01_test.py --project <name>`
- Pipeline: `uv run python scripts/runner/execute_pipeline.py --project <name> --core-only`
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

**Regeneration note:** Refresh [`active_projects.md`](active_projects.md) with `scripts/docgen/active_projects.py`. Re-derive this file with `uv run python scripts/docgen/counts.py --write` after meaningful CI or test-scale changes. Re-run `uv run python scripts/audit/check_template_drift.py --strict` and `uv run python scripts/gates/module_line_count_check.py` when drift or line-count gates change.
"""


def write_counts_doc(
    repo_root: Path,
    out_path: Path | None = None,
    *,
    facts: CountsFacts | None = None,
) -> Path:
    """Render and write COUNTS.md; returns the written path."""
    validate_coverage_provenance(repo_root)
    target = out_path if out_path is not None else repo_root / DOC_RELATIVE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_counts_doc(facts or collect_facts(repo_root)), encoding="utf-8")
    return target


def check_counts_doc(repo_root: Path) -> tuple[bool, str]:
    """Return (in_sync, message) comparing on-disk COUNTS.md with a fresh render."""
    try:
        validate_coverage_provenance(repo_root)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        return False, f"STALE coverage provenance: {exc}"
    doc_path = repo_root / DOC_RELATIVE_PATH
    rendered = render_counts_doc(collect_facts(repo_root))
    on_disk = doc_path.read_text(encoding="utf-8") if doc_path.is_file() else ""
    if rendered == on_disk:
        return True, "COUNTS.md: OK (in sync with live tree)"
    return False, f"STALE: {DOC_RELATIVE_PATH} differs from a fresh render — run --write"
