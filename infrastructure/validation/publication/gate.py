"""Sharded, parallel publication-output gate over per-project audits.

The audit itself is per project (`publication-audit --project`); this module turns
that into the shape a release needs: choose a roster or shard, run each project in
its own process, classify findings by severity, and emit one receipt per project.
It never re-implements the audit checks — it only schedules them and aggregates
their original JSON.

Severity policy:

* ``blocking`` — an ``error`` finding fails the gate; ``review_required`` findings
  are reported and do not fail. This is the fast lane.
* ``strict`` — ``review_required`` findings fail too. This is the release lane.

Selection policy
----------------
``--changed`` narrows the audited roster, so narrowing is only admitted for
evidence that cannot reach another project's publication output:

* An exact public-exemplar path (``projects/templates/<name>/...``) selects that
  exemplar. A manuscript edit is an exemplar source edit, so project ownership
  is resolved before any documentation exemption.
* A documentation path outside ``projects/``, ``infrastructure/`` and
  ``scripts/`` (``docs/**``, root ``*.md``) cannot change rendered bytes; it
  selects nothing and says so.
* Every other path — shared implementation, toolchain, control file, unknown
  top-level path, unknown or non-template project tree — widens the selection to
  the whole baseline roster. A rendered-provenance receipt binds every tracked
  implementation file under ``infrastructure/`` and ``scripts/``, so one stage
  edit invalidates every exemplar's receipt.

An observed empty change set selects nothing. Observation failure raises: the
gate never guesses a clean change set. The peer policy for functional test
selection is :func:`infrastructure.core.testing.ci_selection.affected_projects`;
it additionally expands transitive reverse dependencies, which publication
outputs do not have, and it applies its documentation exemption before project
ownership.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Literal

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

GateMode = Literal["blocking", "strict"]
AUDIT_MODULE = "infrastructure.validation.cli"
SHARED_IMPLEMENTATION_ROOTS = frozenset({"infrastructure", "scripts"})
_DOCUMENTATION_SUFFIXES = frozenset({".md", ".rst", ".txt"})
_SHARD = re.compile(r"^(?P<index>\d+)/(?P<count>[1-9]\d*)$")


@dataclass(frozen=True)
class ProjectGateResult:
    """One project's original audit outcome."""

    project: str
    status: str
    blocking: tuple[str, ...]
    review_required: tuple[str, ...]
    diagnostic: str = ""

    @property
    def failed(self) -> bool:
        """Return whether this project fails under any policy."""
        return bool(self.blocking)


@dataclass(frozen=True)
class ProjectSelection:
    """Resolved audited roster plus the reason that roster was narrowed."""

    projects: tuple[str, ...]
    reason: str
    widened: bool = False


@dataclass(frozen=True)
class PublicationGateReport:
    """Aggregate outcome for the selected roster."""

    mode: GateMode
    results: tuple[ProjectGateResult, ...]
    selection: ProjectSelection = field(default_factory=lambda: ProjectSelection((), "unspecified selection"))

    @property
    def failed(self) -> bool:
        """Return whether the gate fails under its declared severity policy."""
        if self.mode == "strict":
            return any(result.failed or result.review_required for result in self.results)
        return any(result.failed for result in self.results)

    @property
    def blocking_count(self) -> int:
        """Total error-severity findings across the roster."""
        return sum(len(result.blocking) for result in self.results)

    @property
    def review_required_count(self) -> int:
        """Total review-required findings across the roster."""
        return sum(len(result.review_required) for result in self.results)


def _exemplar_scope(path: str, roster: frozenset[str]) -> str | None:
    """Return the exemplar that owns *path*, or ``None`` for any other path."""
    parts = PurePosixPath(path).parts
    if len(parts) < 3 or parts[0] != "projects" or parts[1] != "templates":
        return None
    scope = "/".join(parts[1:3])
    return scope if scope in roster else None


def _documentation_only(path: str) -> bool:
    """Return whether a non-exemplar path is prose that cannot change output bytes."""
    parts = PurePosixPath(path).parts
    if not parts or parts[0] in {"projects", *SHARED_IMPLEMENTATION_ROOTS}:
        return False
    return PurePosixPath(path).suffix.lower() in _DOCUMENTATION_SUFFIXES


def publication_affected_projects(
    changed: tuple[str, ...] | None, *, base: tuple[str, ...] | None = None
) -> ProjectSelection:
    """Resolve the audited roster for an observed change set.

    ``None`` means no changed-path filter was requested. An empty tuple is an
    observed clean change set, which selects nothing. Any path that is not an
    exact public-exemplar path widens the selection to ``base`` because shared
    implementation, toolchain and control changes invalidate every exemplar's
    rendered-provenance receipt.
    """
    roster = frozenset(PUBLIC_PROJECT_NAMES)
    baseline = tuple(sorted(base)) if base is not None else tuple(sorted(roster))
    if changed is None:
        return ProjectSelection(baseline, "no changed-path filter requested")
    paths = tuple(sorted({str(path).replace("\\", "/") for path in changed if str(path).strip()}))
    if not paths:
        return ProjectSelection((), "no observed working-tree changes")
    affected: set[str] = set()
    documentation = 0
    for path in paths:
        scope = _exemplar_scope(path, roster)
        if scope is not None:
            affected.add(scope)
            continue
        if _documentation_only(path):
            documentation += 1
            continue
        return ProjectSelection(
            baseline,
            f"widened to the full roster: shared or unknown change {path} can affect every exemplar",
            widened=True,
        )
    narrowed = tuple(sorted(affected & set(baseline)))
    if not narrowed:
        return ProjectSelection(
            (),
            f"documentation-only change ({documentation} path(s)) cannot change rendered output",
        )
    return ProjectSelection(narrowed, "exact public-exemplar changes only")


def resolve_selection(
    *,
    projects: tuple[str, ...] = (),
    all_public: bool = False,
    changed: tuple[str, ...] | None = None,
) -> ProjectSelection:
    """Resolve an explicit, whole-roster, or changed-path selection with its reason."""
    roster = tuple(sorted(PUBLIC_PROJECT_NAMES))
    if projects:
        unknown = sorted(set(projects) - set(roster))
        if unknown:
            raise ValueError(f"unknown public project(s): {', '.join(unknown)}")
        baseline, reason = tuple(sorted(projects)), "explicit public project selection"
    elif all_public:
        baseline, reason = roster, "whole canonical public roster"
    elif changed is None:
        raise ValueError("select projects explicitly, with --all-public, or with --changed")
    else:
        baseline, reason = roster, "canonical public roster"
    if changed is None:
        return ProjectSelection(baseline, reason)
    if not projects and not all_public and not changed:
        return ProjectSelection((), "no observed working-tree changes")
    return publication_affected_projects(changed, base=baseline)


def select_projects(
    *, projects: tuple[str, ...] = (), all_public: bool, changed: tuple[str, ...] | None = None
) -> tuple[str, ...]:
    """Resolve the audited roster: explicit projects, changed-only, or the whole roster.

    ``changed=None`` applies no filter; ``changed=()`` is an observed clean change
    set and selects nothing.
    """
    return resolve_selection(projects=projects, all_public=all_public, changed=changed).projects


def shard_projects(projects: tuple[str, ...], shard: str) -> tuple[str, ...]:
    """Return one disjoint, complete slice of the roster for a CI matrix cell."""
    match = _SHARD.fullmatch(shard.strip())
    if match is None:
        raise ValueError("--shard must look like INDEX/COUNT, e.g. 0/4")
    index, count = int(match.group("index")), int(match.group("count"))
    if not 0 <= index < count:
        raise ValueError(f"--shard index must be between 0 and {count - 1}")
    return tuple(name for position, name in enumerate(sorted(projects)) if position % count == index)


def changed_project_paths(repo_root: Path) -> tuple[str, ...]:
    """Return working-tree changed paths (staged, unstaged and untracked)."""
    root = Path(repo_root)
    commands = (
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    )
    paths: list[str] = []
    for command in commands:
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
        if result.returncode:
            raise ValueError(f"git refused {command[1]}; refusing to guess changed projects")
        paths.extend(line for line in result.stdout.splitlines() if line)
    return tuple(sorted(set(paths)))


def _audit_project(repo_root: Path, project: str, *, mode: GateMode) -> ProjectGateResult:
    command = [
        sys.executable,
        "-m",
        AUDIT_MODULE,
        "publication-audit",
        "--repo-root",
        str(repo_root),
        "--project",
        project,
        "--rendered",
        "--format",
        "json",
    ]
    result = subprocess.run(command, cwd=repo_root, capture_output=True, text=True, check=False)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return ProjectGateResult(
            project=project,
            status="unknown",
            blocking=("audit did not emit JSON",),
            review_required=(),
            diagnostic=(result.stderr or result.stdout).strip()[-400:],
        )
    findings = payload.get("findings") or []
    blocking = tuple(
        sorted({str(finding.get("diagnostic_code")) for finding in findings if finding.get("severity") == "error"})
    )
    review = tuple(
        sorted({str(finding.get("diagnostic_code")) for finding in findings if finding.get("severity") != "error"})
    )
    return ProjectGateResult(
        project=project,
        status=str(payload.get("status", "unknown")),
        blocking=blocking,
        review_required=review,
    )


def run_publication_gate(
    repo_root: Path,
    projects: tuple[str, ...],
    *,
    mode: GateMode = "blocking",
    jobs: int = 1,
    selection: ProjectSelection | None = None,
) -> PublicationGateReport:
    """Audit every selected project, at most ``jobs`` at a time."""
    root = Path(repo_root).resolve()
    workers = max(1, min(jobs, len(projects) or 1))
    if workers == 1:
        results = tuple(_audit_project(root, project, mode=mode) for project in projects)
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = tuple(pool.map(lambda name: _audit_project(root, name, mode=mode), projects))
    resolved = selection or ProjectSelection(tuple(projects), "unspecified selection")
    return PublicationGateReport(mode=mode, results=results, selection=resolved)


def write_receipts(report: PublicationGateReport, directory: Path) -> tuple[Path, ...]:
    """Write one JSON receipt per project and return the paths written.

    Each receipt records the selection that produced it, so a narrowed
    ``--changed`` run cannot be presented later as a whole-roster pass.
    """
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for result in report.results:
        path = directory / f"{Path(result.project).name}.json"
        payload = {
            "schema_version": "template-publication-gate/v2",
            "project": result.project,
            "mode": report.mode,
            "status": "fail" if (result.failed or (report.mode == "strict" and result.review_required)) else "pass",
            "audit_status": result.status,
            "blocking_codes": list(result.blocking),
            "review_required_codes": list(result.review_required),
            "selection": {
                "reason": report.selection.reason,
                "widened": report.selection.widened,
                "roster_size": len(report.selection.projects),
            },
            "diagnostic": result.diagnostic,
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)
    return tuple(written)


def format_gate_report(report: PublicationGateReport) -> str:
    """Render a compact, actionable summary grouped by diagnostic code."""
    if not report.results:
        return (
            f"publication outputs: skipped — nothing audited ({report.selection.reason}); "
            "this is not a passing audit of the roster"
        )
    failed = [
        result for result in report.results if result.failed or (report.mode == "strict" and result.review_required)
    ]
    lines = [
        f"publication outputs: {len(report.results)} project(s), mode={report.mode}, "
        f"blocking={report.blocking_count}, review_required={report.review_required_count} "
        f"[{report.selection.reason}]"
    ]
    if not failed:
        lines.append("status: pass")
        return "\n".join(lines)
    lines.append(f"status: fail ({len(failed)} project(s))")
    by_code: dict[str, list[str]] = {}
    for result in failed:
        for code in (*result.blocking, *(result.review_required if report.mode == "strict" else ())):
            by_code.setdefault(code, []).append(Path(result.project).name)
    for code in sorted(by_code):
        names = sorted(by_code[code])
        shown = ", ".join(names[:6]) + (f" (+{len(names) - 6} more)" if len(names) > 6 else "")
        lines.append(f"  {code}: {len(names)} project(s) — {shown}")
    lines.append(
        "remediation: scripts/pipeline/stage_04_validate.py --project <name>, then stage the evidence it writes"
    )
    return "\n".join(lines)


__all__ = [
    "GateMode",
    "ProjectGateResult",
    "ProjectSelection",
    "PublicationGateReport",
    "changed_project_paths",
    "format_gate_report",
    "publication_affected_projects",
    "resolve_selection",
    "run_publication_gate",
    "select_projects",
    "shard_projects",
    "write_receipts",
]
