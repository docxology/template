"""Doctor detectors — Workspace hygiene checks."""

from __future__ import annotations

from pathlib import Path

from infrastructure.doctor.models import Finding, RepairLevel, Severity, TherapyLevel

_CACHE_DIRS = ("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache")


def detect_pycache_clutter(repo_root: Path) -> list[Finding]:
    """Locate __pycache__ and tool caches anywhere under the repo.

    These never break a build — they're disposable — but cleaning them
    cures the most common mysterious test-import bug ("why is pytest
    finding a stale module").
    """
    found: list[Path] = []
    scan_roots = (
        repo_root / "infrastructure",
        repo_root / "projects",
        repo_root / "scripts",
        repo_root / "tests",
    )
    dormant_project_subdirs = {"archive", "other", "published", "working"}
    for scan_root in scan_roots:
        if not scan_root.is_dir():
            continue
        for sub in scan_root.rglob("*"):
            if not sub.is_dir():
                continue
            if sub.name not in _CACHE_DIRS:
                continue
            try:
                rel_parts = sub.relative_to(repo_root).parts
            except ValueError:
                continue
            if len(rel_parts) >= 2 and rel_parts[0] == "projects" and rel_parts[1] in dormant_project_subdirs:
                continue
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

        discovered = discover_projects(repo_root)
        known = {p.qualified_name.split("/")[-1] for p in discovered}
        known |= {p.qualified_name for p in discovered}
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
