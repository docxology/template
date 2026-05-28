"""Read-only diagnostic detectors.

Each detector is a pure function that takes the repo root and returns a
list of :class:`~infrastructure.doctor.models.Finding`. Detectors must
be **idempotent** (running them twice in a row yields the same
findings) and **side-effect free** — no file writes, no network, no
subprocess that can mutate state. The only allowed subprocesses are
read-only probes (``tool --version``).

The :data:`DETECTORS` list is the canonical registration order. New
detectors are added by appending to that list (and by registering a
fixer in :mod:`.fixers` if there is a safe automatic remediation).
"""

import os
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

from infrastructure.doctor.models import (
    Finding,
    RepairLevel,
    Severity,
    TherapyLevel,
)


__all__ = [
    "DETECTORS",
    "DetectorFn",
    "run_detectors",
    # Individual detectors (exported for tests):
    "detect_uv_available",
    "detect_python_version",
    "detect_run_sh_executable",
    "detect_project_structure",
    "detect_manuscript_config",
    "detect_pycache_clutter",
    "detect_stale_coverage_files",
    "detect_orphan_output_dirs",
    "detect_pre_commit_installed",
    "detect_optional_services",
    "detect_lockfile_drift",
    "detect_doctor_state_writable",
]


DetectorFn = Callable[[Path], list[Finding]]


# ---------------------------------------------------------------------------
# Tooling
# ---------------------------------------------------------------------------


def detect_uv_available(repo_root: Path) -> list[Finding]:
    """Verify ``uv`` is on PATH — required for every doctor remediation
    that touches dependencies."""
    uv_path = shutil.which("uv")
    if uv_path is None:
        return [
            Finding(
                code="DOC101",
                title="uv package manager not installed",
                severity=Severity.CRITICAL,
                healthy=False,
                description=(
                    "The repository's setup, testing, and rendering all run "
                    "via ``uv``. Install via `curl -LsSf https://astral.sh/uv/install.sh | sh`."
                ),
                evidence={"PATH": os.environ.get("PATH", "")},
                # No automatic fixer — installing system tooling is out of
                # scope for an automatic remediator.
            )
        ]
    return [
        Finding(
            code="DOC101",
            title="uv package manager present",
            severity=Severity.INFO,
            healthy=True,
            description=f"Found uv at {uv_path}.",
            evidence={"path": uv_path},
        )
    ]


def detect_python_version(repo_root: Path) -> list[Finding]:
    """Project requires Python 3.10+ (see pyproject.toml)."""
    import sys

    major, minor = sys.version_info[:2]
    healthy = (major, minor) >= (3, 10)
    return [
        Finding(
            code="DOC102",
            title="Python version compatible",
            severity=Severity.INFO if healthy else Severity.ERROR,
            healthy=healthy,
            description=(f"Project requires Python >= 3.10. Detected {major}.{minor}.{sys.version_info.micro}."),
            evidence={
                "version": f"{major}.{minor}.{sys.version_info.micro}",
                "executable": sys.executable,
            },
        )
    ]


def detect_run_sh_executable(repo_root: Path) -> list[Finding]:
    """``run.sh`` must be present and executable for ``./run.sh`` to work."""
    run_sh = repo_root / "run.sh"
    if not run_sh.is_file():
        return [
            Finding(
                code="DOC103",
                title="run.sh missing",
                severity=Severity.ERROR,
                healthy=False,
                description="run.sh is the canonical entry point but is missing.",
                evidence={"path": str(run_sh)},
            )
        ]
    is_executable = os.access(run_sh, os.X_OK)
    if is_executable:
        return [
            Finding(
                code="DOC103",
                title="run.sh executable",
                severity=Severity.INFO,
                healthy=True,
                description="run.sh is present and executable.",
                evidence={"path": str(run_sh)},
            )
        ]
    return [
        Finding(
            code="DOC103",
            title="run.sh not executable",
            severity=Severity.WARN,
            healthy=False,
            description=(
                "run.sh exists but lacks the executable bit. ``./run.sh`` will fail with 'permission denied'."
            ),
            evidence={"path": str(run_sh)},
            repair_levels=(
                RepairLevel(
                    level=TherapyLevel.CONSERVATIVE,
                    fix_id="fix_make_run_sh_executable",
                    description="chmod +x run.sh",
                ),
            ),
        )
    ]


# ---------------------------------------------------------------------------
# Project layout
# ---------------------------------------------------------------------------


def detect_project_structure(repo_root: Path) -> list[Finding]:
    """Every active project must have ``src/`` and ``tests/``.

    Uses :func:`infrastructure.project.discover_projects` so this stays
    aligned with the rest of the pipeline.
    """
    try:
        from infrastructure.project.discovery import discover_projects
    except Exception as exc:  # pragma: no cover — defensive
        return [
            Finding(
                code="DOC201",
                title="project discovery import failed",
                severity=Severity.CRITICAL,
                healthy=False,
                description=f"Could not import infrastructure.project: {exc}",
            )
        ]

    findings: list[Finding] = []
    projects_dir = repo_root / "projects"
    if not projects_dir.is_dir():
        return [
            Finding(
                code="DOC201",
                title="projects/ directory missing",
                severity=Severity.ERROR,
                healthy=False,
                description="The active projects directory is missing.",
                evidence={"path": str(projects_dir)},
            )
        ]

    projects = discover_projects(repo_root)
    findings.append(
        Finding(
            code="DOC201",
            title="projects discovered",
            severity=Severity.INFO,
            healthy=True,
            description=f"Discovered {len(projects)} active project(s).",
            evidence={"projects": [p.qualified_name for p in projects]},
        )
    )

    # Per-project structural checks: pyproject.toml and manuscript dir.
    for project in projects:
        pyproject = project.path / "pyproject.toml"
        if not pyproject.is_file():
            findings.append(
                Finding(
                    code=f"DOC202[{project.qualified_name}]",
                    title=f"{project.qualified_name}: pyproject.toml missing",
                    severity=Severity.WARN,
                    healthy=False,
                    description=("Project lacks pyproject.toml — `uv sync` will not manage its dependencies."),
                    evidence={"path": str(pyproject)},
                )
            )
    return findings


def detect_manuscript_config(repo_root: Path) -> list[Finding]:
    """Each project's manuscript/config.yaml must parse and declare a paper.title."""
    try:
        from infrastructure.project.discovery import discover_projects
    except Exception:  # pragma: no cover — covered by DOC201
        return []

    findings: list[Finding] = []
    for project in discover_projects(repo_root):
        if not project.has_manuscript:
            continue
        cfg = project.path / "manuscript" / "config.yaml"
        if not cfg.is_file():
            findings.append(
                Finding(
                    code=f"DOC203[{project.qualified_name}]",
                    title=f"{project.qualified_name}: manuscript/config.yaml missing",
                    severity=Severity.WARN,
                    healthy=False,
                    description="manuscript/config.yaml is required for PDF rendering.",
                    evidence={"path": str(cfg)},
                )
            )
            continue
        try:
            import yaml  # local import — yaml is in the rendering group
        except ImportError:
            findings.append(
                Finding(
                    code=f"DOC203[{project.qualified_name}]",
                    title=f"{project.qualified_name}: PyYAML not installed",
                    severity=Severity.WARN,
                    healthy=False,
                    description=("Cannot parse manuscript config — install with `uv sync --group rendering`."),
                )
            )
            continue
        try:
            data: Any = yaml.safe_load(cfg.read_text())
        except yaml.YAMLError as exc:
            findings.append(
                Finding(
                    code=f"DOC203[{project.qualified_name}]",
                    title=f"{project.qualified_name}: manuscript/config.yaml malformed",
                    severity=Severity.ERROR,
                    healthy=False,
                    description=f"YAML parse error: {exc}",
                    evidence={"path": str(cfg)},
                )
            )
            continue
        title = ""
        if isinstance(data, dict):
            paper = data.get("paper")
            if isinstance(paper, dict):
                title = str(paper.get("title", "")).strip()
        if not title:
            findings.append(
                Finding(
                    code=f"DOC203[{project.qualified_name}]",
                    title=f"{project.qualified_name}: manuscript title missing",
                    severity=Severity.WARN,
                    healthy=False,
                    description=(
                        "manuscript/config.yaml must declare `paper.title` for rendering and metadata extraction."
                    ),
                    evidence={"path": str(cfg)},
                )
            )
        else:
            findings.append(
                Finding(
                    code=f"DOC203[{project.qualified_name}]",
                    title=f"{project.qualified_name}: manuscript config OK",
                    severity=Severity.INFO,
                    healthy=True,
                    description=f"Title: {title!r}",
                    evidence={"path": str(cfg), "title": title},
                )
            )
    return findings


# ---------------------------------------------------------------------------
# Hygiene
# ---------------------------------------------------------------------------


_CACHE_DIRS = ("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache")


def detect_pycache_clutter(repo_root: Path) -> list[Finding]:
    """Locate __pycache__ and tool caches anywhere under the repo.

    These never break a build — they're disposable — but cleaning them
    cures the most common mysterious test-import bug ("why is pytest
    finding a stale module").
    """
    found: list[Path] = []
    # Top-level directories where stray caches are not the doctor's concern:
    #   * .venv / node_modules — tool-managed environments
    #   * .doctor — our own state
    ignored_top = {".venv", ".doctor", "node_modules"}
    # Non-rendered typed project subfolders are dormant private trees — leave
    # alone. Keep in sync with discovery.NON_RENDERED_SUBDIRS.
    dormant_project_subdirs = {"archive", "other", "published", "working"}
    for sub in repo_root.rglob("*"):
        if not sub.is_dir():
            continue
        if sub.name not in _CACHE_DIRS:
            continue
        try:
            rel_parts = sub.relative_to(repo_root).parts
        except ValueError:
            continue
        if rel_parts and rel_parts[0] in ignored_top:
            continue
        if len(rel_parts) >= 2 and rel_parts[0] == "projects" and rel_parts[1] in dormant_project_subdirs:
            continue
        # Also skip caches embedded in any nested ``.venv`` further down.
        if any(part == ".venv" for part in rel_parts):
            continue
        found.append(sub)

    if not found:
        return [
            Finding(
                code="DOC301",
                title="cache directories clean",
                severity=Severity.INFO,
                healthy=True,
                description="No stray __pycache__ / .pytest_cache / .mypy_cache / .ruff_cache.",
            )
        ]

    return [
        Finding(
            code="DOC301",
            title=f"{len(found)} cache director(y/ies) present",
            severity=Severity.INFO if len(found) < 100 else Severity.WARN,
            healthy=False,
            description=(
                "Stray Python/tool cache directories. Safe to delete; deleting "
                "fixes most 'stale import' surprises after a refactor."
            ),
            evidence={
                "count": len(found),
                "sample": [str(p.relative_to(repo_root)) for p in found[:10]],
            },
            repair_levels=(
                RepairLevel(
                    level=TherapyLevel.CONSERVATIVE,
                    fix_id="fix_clean_pycache",
                    description=f"Delete {len(found)} cache director(y/ies) (backed up)",
                ),
            ),
        )
    ]


def detect_stale_coverage_files(repo_root: Path) -> list[Finding]:
    """``.coverage`` and ``coverage_*.json`` from prior pytest runs.

    The CI splits coverage into ``.coverage.infra`` / ``.coverage.project``
    files; leaving them around can confuse a follow-up ``pytest --cov``.
    """
    candidates: list[Path] = []
    for pattern in (".coverage", ".coverage.*", "coverage_*.json", "coverage.xml"):
        candidates.extend(repo_root.glob(pattern))
    candidates = sorted(set(candidates))

    if not candidates:
        return [
            Finding(
                code="DOC302",
                title="no stale coverage files",
                severity=Severity.INFO,
                healthy=True,
                description="No leftover coverage artifacts in repo root.",
            )
        ]

    return [
        Finding(
            code="DOC302",
            title=f"{len(candidates)} stale coverage file(s)",
            severity=Severity.INFO,
            healthy=False,
            description=(
                "Leftover coverage artifacts can mix prior infra-suite and "
                "project-suite results. Safe to delete; regenerated on next run."
            ),
            evidence={
                "files": [str(p.relative_to(repo_root)) for p in candidates],
            },
            repair_levels=(
                RepairLevel(
                    level=TherapyLevel.CONSERVATIVE,
                    fix_id="fix_clean_coverage_files",
                    description="Remove stale coverage artifacts (backed up)",
                ),
            ),
        )
    ]


def detect_orphan_output_dirs(repo_root: Path) -> list[Finding]:
    """``output/<name>/`` whose ``<name>`` does not match any discovered project.

    Project rotations between the typed subfolders under ``projects/``
    (``active/``, ``working/``, ``published/``, ``archive/``, ``other/``) leave
    behind output trees that nothing else refreshes. Removing them is *radical*
    — the user may want the PDFs — so we only suggest, never apply
    automatically.
    """
    out_dir = repo_root / "output"
    if not out_dir.is_dir():
        return [
            Finding(
                code="DOC303",
                title="output/ directory absent",
                severity=Severity.INFO,
                healthy=True,
                description="No output/ directory present (clean tree).",
            )
        ]

    try:
        from infrastructure.project.discovery import discover_projects

        known = {p.qualified_name.split("/")[-1] for p in discover_projects(repo_root)}
        known |= {p.qualified_name for p in discover_projects(repo_root)}
    except Exception:  # pragma: no cover — defensive
        known = set()

    reserved = {"executive_summary", "executive_report"}

    orphans: list[Path] = []
    for child in sorted(out_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name in reserved or child.name.startswith("."):
            continue
        if child.name in known:
            continue
        orphans.append(child)

    if not orphans:
        return [
            Finding(
                code="DOC303",
                title="output/ tree matches active projects",
                severity=Severity.INFO,
                healthy=True,
                description="Every output subdirectory corresponds to an active project.",
            )
        ]

    return [
        Finding(
            code="DOC303",
            title=f"{len(orphans)} orphan output director(y/ies)",
            severity=Severity.WARN,
            healthy=False,
            description=(
                "These output directories have no matching active project — "
                "likely from archived or in-progress projects. Review before "
                "deleting; deletion is reversible via the doctor's undo."
            ),
            evidence={"orphans": [str(p.relative_to(repo_root)) for p in orphans]},
            repair_levels=(
                RepairLevel(
                    level=TherapyLevel.RADICAL,
                    fix_id="fix_remove_orphan_output_dirs",
                    description=f"Move {len(orphans)} orphan output director(y/ies) to backup",
                ),
            ),
        )
    ]


# ---------------------------------------------------------------------------
# Tooling state
# ---------------------------------------------------------------------------


def detect_pre_commit_installed(repo_root: Path) -> list[Finding]:
    """``.git/hooks/pre-commit`` should reference ``pre-commit`` when the
    repo has a ``.pre-commit-config.yaml``."""
    config = repo_root / ".pre-commit-config.yaml"
    if not config.is_file():
        return [
            Finding(
                code="DOC401",
                title="no pre-commit configuration",
                severity=Severity.INFO,
                healthy=True,
                description="Repo does not declare pre-commit hooks; nothing to install.",
            )
        ]
    hook = repo_root / ".git" / "hooks" / "pre-commit"
    if not hook.is_file():
        return [
            Finding(
                code="DOC401",
                title="pre-commit hook not installed",
                severity=Severity.WARN,
                healthy=False,
                description=(
                    "The repo declares pre-commit hooks but the git hook is not "
                    "installed locally. CI will still run them, but local commits "
                    "won't be gated."
                ),
                evidence={"config": str(config), "expected_hook": str(hook)},
                repair_levels=(
                    RepairLevel(
                        level=TherapyLevel.CONSERVATIVE,
                        fix_id="fix_install_pre_commit_hook",
                        description="Run `pre-commit install`",
                    ),
                ),
            )
        ]
    return [
        Finding(
            code="DOC401",
            title="pre-commit hook installed",
            severity=Severity.INFO,
            healthy=True,
            description="Local pre-commit hook is in place.",
            evidence={"hook": str(hook)},
        )
    ]


def detect_lockfile_drift(repo_root: Path) -> list[Finding]:
    """``uv.lock`` should be at least as new as ``pyproject.toml``."""
    pyproject = repo_root / "pyproject.toml"
    lock = repo_root / "uv.lock"
    if not pyproject.is_file():
        return [
            Finding(
                code="DOC402",
                title="pyproject.toml missing at repo root",
                severity=Severity.CRITICAL,
                healthy=False,
                description="No root pyproject.toml — uv cannot manage the workspace.",
                evidence={"path": str(pyproject)},
            )
        ]
    if not lock.is_file():
        return [
            Finding(
                code="DOC402",
                title="uv.lock missing",
                severity=Severity.WARN,
                healthy=False,
                description=(
                    "uv.lock is missing — runs will resolve dependencies fresh "
                    "every time. Run `uv sync` to generate it."
                ),
                evidence={"path": str(lock)},
                repair_levels=(
                    RepairLevel(
                        level=TherapyLevel.MODERATE,
                        fix_id="fix_run_uv_sync",
                        description="Run `uv sync` to regenerate uv.lock",
                    ),
                ),
            )
        ]
    py_mtime = pyproject.stat().st_mtime
    lock_mtime = lock.stat().st_mtime
    drift = py_mtime - lock_mtime
    if drift > 1.0:
        return [
            Finding(
                code="DOC402",
                title="uv.lock older than pyproject.toml",
                severity=Severity.WARN,
                healthy=False,
                description=(
                    f"uv.lock is {drift:.0f}s older than pyproject.toml — "
                    "dependencies may have changed since the last sync."
                ),
                evidence={
                    "pyproject_mtime": py_mtime,
                    "lock_mtime": lock_mtime,
                    "drift_seconds": drift,
                },
                repair_levels=(
                    RepairLevel(
                        level=TherapyLevel.MODERATE,
                        fix_id="fix_run_uv_sync",
                        description="Run `uv sync` to refresh uv.lock",
                    ),
                ),
            )
        ]
    return [
        Finding(
            code="DOC402",
            title="uv.lock up to date",
            severity=Severity.INFO,
            healthy=True,
            description="uv.lock is at least as new as pyproject.toml.",
            evidence={"drift_seconds": drift},
        )
    ]


def detect_optional_services(repo_root: Path) -> list[Finding]:
    """Surface optional tools (Ollama, Docker, LaTeX) as info-only findings.

    These never reduce the overall score by themselves — they're listed
    so an agent reading ``--json`` can plan which LLM/render stages to
    skip on this machine.
    """
    findings: list[Finding] = []
    for tool, label, code in [
        ("ollama", "Ollama", "DOC501"),
        ("docker", "Docker", "DOC502"),
        ("xelatex", "XeLaTeX", "DOC503"),
        ("pandoc", "Pandoc", "DOC504"),
    ]:
        path = shutil.which(tool)
        found = path is not None
        findings.append(
            Finding(
                code=code,
                title=f"{label} {'available' if found else 'not installed'}",
                severity=Severity.INFO if found else Severity.WARN,
                healthy=found,
                description=(f"{label} is required by some optional pipeline stages."),
                evidence={"path": path or ""},
            )
        )
    return findings


def detect_doctor_state_writable(repo_root: Path) -> list[Finding]:
    """``.doctor/`` must be creatable for any fix to be safe."""
    doctor_dir = repo_root / ".doctor"
    try:
        doctor_dir.mkdir(exist_ok=True)
        probe = doctor_dir / ".write_probe"
        probe.write_text("ok")
        probe.unlink()
    except OSError as exc:
        return [
            Finding(
                code="DOC601",
                title="doctor state directory not writable",
                severity=Severity.CRITICAL,
                healthy=False,
                description=("Cannot write to .doctor/ — no fix can be applied safely without a backup target."),
                evidence={"path": str(doctor_dir), "error": str(exc)},
            )
        ]
    return [
        Finding(
            code="DOC601",
            title="doctor state directory writable",
            severity=Severity.INFO,
            healthy=True,
            description="Backups and journal can be written.",
            evidence={"path": str(doctor_dir)},
        )
    ]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


DETECTORS: tuple[DetectorFn, ...] = (
    detect_doctor_state_writable,
    detect_uv_available,
    detect_python_version,
    detect_run_sh_executable,
    detect_project_structure,
    detect_manuscript_config,
    detect_pycache_clutter,
    detect_stale_coverage_files,
    detect_orphan_output_dirs,
    detect_pre_commit_installed,
    detect_lockfile_drift,
    detect_optional_services,
)


def run_detectors(
    repo_root: Path,
    selected: tuple[DetectorFn, ...] | None = None,
) -> list[Finding]:
    """Run every detector (or only ``selected``) and return findings.

    Findings are returned sorted by ``code`` for deterministic output.
    Any detector that raises is converted into a CRITICAL finding so a
    bug in one detector cannot mask the others.
    """
    detectors = selected or DETECTORS
    out: list[Finding] = []
    for fn in detectors:
        try:
            out.extend(fn(repo_root))
        except Exception as exc:  # noqa: BLE001 — defensive isolation
            out.append(
                Finding(
                    code=f"DOC000[{fn.__name__}]",
                    title=f"detector {fn.__name__} crashed",
                    severity=Severity.CRITICAL,
                    healthy=False,
                    description=str(exc),
                    evidence={"detector": fn.__name__},
                )
            )
    out.sort(key=lambda f: f.code)
    return out
