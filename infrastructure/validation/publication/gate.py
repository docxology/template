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
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

GateMode = Literal["blocking", "strict"]
AUDIT_MODULE = "infrastructure.validation.cli"
_SHARD = re.compile(r"^(?P<index>\d+)/(?P<count>[1-9]\d*)$")


@dataclass(frozen=True)
class ProjectGateResult:
    """One project's original audit outcome."""

    project: str
    status: str
    blocking: tuple[str, ...]
    review_required: tuple[str, ...]
    diagnostic: str = ""
    original_exit: int | None = None

    @property
    def failed(self) -> bool:
        """Return whether this project fails under any policy."""
        return bool(self.blocking) or self.status not in {"pass", "review"} or self.original_exit not in (None, 0)


@dataclass(frozen=True)
class PublicationGateReport:
    """Aggregate outcome for the selected roster."""

    mode: GateMode
    results: tuple[ProjectGateResult, ...]

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


def select_projects(
    *, projects: tuple[str, ...] = (), all_public: bool, changed: tuple[str, ...] = ()
) -> tuple[str, ...]:
    """Resolve the roster: explicit projects, changed-only, or the whole public roster."""
    roster = tuple(PUBLIC_PROJECT_NAMES)
    if projects:
        unknown = sorted(set(projects) - set(roster))
        if unknown:
            raise ValueError(f"unknown public project(s): {', '.join(unknown)}")
        selected = projects
    else:
        selected = roster
    if changed:
        wanted = {name for name in selected if any(path.startswith(f"projects/{name}/") for path in changed)}
        selected = tuple(sorted(wanted))
    if not all_public and not projects and not changed:
        raise ValueError("select projects explicitly, with --all-public, or with --changed")
    return tuple(sorted(selected))


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
    return _audit_result(project, result)


def _audit_result(project: str, result: subprocess.CompletedProcess[str]) -> ProjectGateResult:
    """Admit current audit JSON without allowing it to erase its original exit."""
    blocking = {"PUBLICATION.AUDIT_SUBPROCESS_FAILED"} if result.returncode else set()
    diagnostic = f"audit subprocess exited with status {result.returncode}" if result.returncode else ""

    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("audit JSON repeats a field")
            value[key] = item
        return value

    try:
        payload = json.loads(result.stdout, object_pairs_hook=unique_object)
        if (
            not isinstance(payload, dict)
            or set(payload) != {"schema_version", "status", "projects", "summary", "findings"}
            or payload["schema_version"] != "template-publication-audit-v1"
            or payload["projects"] != [project]
            or payload["status"] not in {"pass", "review", "fail"}
            or not isinstance(payload["findings"], list)
        ):
            raise ValueError("audit report schema, project or status is invalid")
        findings = payload["findings"]
        fields = {
            "project",
            "path",
            "diagnostic_code",
            "severity",
            "status",
            "message",
            "evidence",
            "remediation",
            "line",
        }
        for finding in findings:
            if (
                not isinstance(finding, dict)
                or set(finding) != fields
                or any(not isinstance(finding[key], str) for key in fields - {"line"})
                or finding["project"] != project
                or not finding["diagnostic_code"]
                or (finding["severity"], finding["status"]) not in {("error", "fail"), ("warning", "review_required")}
                or type(finding["line"]) is not int
                or finding["line"] < 0
            ):
                raise ValueError("audit finding is malformed or belongs to another project")
        errors = [finding for finding in findings if finding["status"] == "fail"]
        reviews = [finding for finding in findings if finding["status"] == "review_required"]
        expected_summary = {
            "finding_count": len(findings),
            "blocking_count": len(errors),
            "review_required_count": len(reviews),
        }
        summary = payload["summary"]
        if (
            not isinstance(summary, dict)
            or summary != expected_summary
            or any(type(value) is not int for value in summary.values())
            or payload["status"] != ("fail" if errors else "review" if reviews else "pass")
        ):
            raise ValueError("audit summary or status disagrees with its findings")
    except (ValueError, TypeError) as error:
        blocking.add("PUBLICATION.AUDIT_INVALID_REPORT")
        return ProjectGateResult(
            project=project,
            status="unknown",
            blocking=tuple(sorted(blocking)),
            review_required=(),
            diagnostic="; ".join(part for part in (diagnostic, str(error)) if part),
            original_exit=result.returncode,
        )
    blocking.update(finding["diagnostic_code"] for finding in errors)
    return ProjectGateResult(
        project=project,
        status=payload["status"],
        blocking=tuple(sorted(blocking)),
        review_required=tuple(sorted({finding["diagnostic_code"] for finding in reviews})),
        diagnostic=diagnostic,
        original_exit=result.returncode,
    )


def run_publication_gate(
    repo_root: Path,
    projects: tuple[str, ...],
    *,
    mode: GateMode = "blocking",
    jobs: int = 1,
) -> PublicationGateReport:
    """Audit every selected project, at most ``jobs`` at a time."""
    root = Path(repo_root).resolve()
    workers = max(1, min(jobs, len(projects) or 1))
    if workers == 1:
        results = tuple(_audit_project(root, project, mode=mode) for project in projects)
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = tuple(pool.map(lambda name: _audit_project(root, name, mode=mode), projects))
    return PublicationGateReport(mode=mode, results=results)


def write_receipts(report: PublicationGateReport, directory: Path) -> tuple[Path, ...]:
    """Write one JSON receipt per project and return the paths written."""
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
            "original_exit": result.original_exit,
            "blocking_codes": list(result.blocking),
            "review_required_codes": list(result.review_required),
            "diagnostic": result.diagnostic,
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)
    return tuple(written)


def format_gate_report(report: PublicationGateReport) -> str:
    """Render a compact, actionable summary grouped by diagnostic code."""
    failed = [
        result for result in report.results if result.failed or (report.mode == "strict" and result.review_required)
    ]
    lines = [
        f"publication outputs: {len(report.results)} project(s), mode={report.mode}, "
        f"blocking={report.blocking_count}, review_required={report.review_required_count}"
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
    "PublicationGateReport",
    "changed_project_paths",
    "format_gate_report",
    "run_publication_gate",
    "select_projects",
    "shard_projects",
    "write_receipts",
]
