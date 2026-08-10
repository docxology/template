"""Machine-checkable contracts for the public future-work backlogs.

The repository intentionally keeps implementation backlogs next to the
canonical root and exemplar projects. This module validates the parts that
must remain mechanically reliable without turning prose planning into an
issue tracker: required sections, unique stable identifiers, and the absence
of references to projects outside the public roster.

Historical evidence is reported as a warning during migration and is blocking
under ``--strict``; the canonical public backlogs are expected to contain only
future work after the migration window.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

Severity = Literal["error", "warning"]

_HEADING_ID = re.compile(r"^#{3,4}\s+`?([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)`?(?:\s|$)")
_TABLE_ID = re.compile(r"^\s*\|\s*`?([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)`?\s*\|")
_HISTORICAL_HEADING = re.compile(
    r"^#{2,3}\s+(?:Shipped|Log|Pass(?: log)?|Fixes completed|Review fixes|Accuracy pass|"
    r"Historical evidence|Still open|Round(?:-|\s)|Measured|20\d{2})\b",
    re.IGNORECASE,
)
_ROTATING_PROJECT = re.compile(r"projects/(?:active|working|ongoing|archive|published|other)/")
_BACKLOG_TABLE_HEADER = (
    "id",
    "size",
    "dependency",
    "proving artifact",
    "acceptance command",
    "negative control",
)
_REQUIRED_EXEMPLAR_SECTIONS = (
    "Integrity and template-status gaps",
    "Configurable-surface gaps",
    "Documentation and signposting gaps",
    "Test and validator gaps",
    "Minor upcoming",
    "Medium upcoming",
    "Major upcoming",
)
_REMOVED_HISTORY_SECTION = re.compile(
    r"^##\s+(?:Current validation evidence|Ordered improvement ladder|Promotion Rule|"
    r"Promotion rule|Active backlog index)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class BacklogFinding:
    """One location-based backlog contract finding."""

    path: Path
    line: int
    severity: Severity
    rule: str
    message: str


@dataclass(frozen=True)
class BacklogReport:
    """Structured result for a root-plus-public-exemplar backlog scan."""

    files: tuple[Path, ...]
    findings: tuple[BacklogFinding, ...]
    identifiers: dict[Path, tuple[str, ...]]

    @property
    def errors(self) -> tuple[BacklogFinding, ...]:
        """Return blocking findings."""
        return tuple(finding for finding in self.findings if finding.severity == "error")

    @property
    def warnings(self) -> tuple[BacklogFinding, ...]:
        """Return advisory findings."""
        return tuple(finding for finding in self.findings if finding.severity == "warning")


def public_backlog_paths(
    repo_root: Path,
    *,
    public_names: Iterable[str] = PUBLIC_PROJECT_NAMES,
) -> tuple[Path, ...]:
    """Return the root TODO plus the TODO for every present public exemplar."""
    root = repo_root.resolve()
    paths = [root / "TO-DO.md"]
    for qualified_name in public_names:
        candidate = root / "projects" / qualified_name / "TODO.md"
        if candidate.is_file():
            paths.append(candidate)
    return tuple(paths)


def _finding(path: Path, line: int, severity: Severity, rule: str, message: str) -> BacklogFinding:
    return BacklogFinding(path=path, line=line, severity=severity, rule=rule, message=message)


def _validate_file(
    path: Path,
    *,
    is_root: bool,
    public_names: Iterable[str],
) -> tuple[list[BacklogFinding], tuple[str, ...]]:
    findings: list[BacklogFinding] = []
    identifiers: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return ([_finding(path, 1, "error", "readable", f"cannot read backlog: {exc}")], ())

    if not lines or not lines[0].startswith("#"):
        findings.append(_finding(path, 1, "error", "heading", "backlog must begin with a Markdown heading"))
    joined = "\n".join(lines)
    if not re.search(r"\b(?:future-only|forward-only|future work|backlog)\b", joined, re.IGNORECASE):
        findings.append(
            _finding(path, 1, "error", "future_only", "backlog must state that it contains future work only")
        )

    required = ("Live baseline and constraints", "Backlog operating rules") if is_root else _REQUIRED_EXEMPLAR_SECTIONS
    headings = {line.lstrip("# ").strip() for line in lines if line.startswith("## ")}
    for section in required:
        if section not in headings:
            findings.append(_finding(path, 1, "error", "required_section", f"missing required section: {section}"))

    has_backlog_table = False
    for line_number, line in enumerate(lines, start=1):
        if line.startswith("|"):
            cells = tuple(cell.strip().casefold() for cell in line.strip().strip("|").split("|"))
            if cells == _BACKLOG_TABLE_HEADER:
                has_backlog_table = True
        # Count declarations, not prose references. This keeps acceptance
        # criteria and dependency graphs from looking like duplicate rows.
        heading_match = _HEADING_ID.match(line)
        table_match = _TABLE_ID.match(line)
        if heading_match:
            identifiers.append(heading_match.group(1))
        if table_match:
            identifiers.append(table_match.group(1))
            cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
            if len(cells) != len(_BACKLOG_TABLE_HEADER):
                findings.append(
                    _finding(
                        path,
                        line_number,
                        "error",
                        "backlog_row_shape",
                        "stable backlog rows must have ID, size, dependency, proving artifact, "
                        "acceptance command, and negative control",
                    )
                )
            else:
                empty_fields = [
                    field for field, value in zip(_BACKLOG_TABLE_HEADER, cells) if not value or set(value) <= {"-", "—"}
                ]
                if empty_fields:
                    findings.append(
                        _finding(
                            path,
                            line_number,
                            "error",
                            "empty_scope",
                            f"stable backlog row has empty field(s): {', '.join(empty_fields)}",
                        )
                    )
        if _HISTORICAL_HEADING.match(line):
            findings.append(
                _finding(
                    path,
                    line_number,
                    "warning",
                    "historical_section",
                    "completed or dated evidence should move to CHANGELOG.md or a review record",
                )
            )
        if _REMOVED_HISTORY_SECTION.match(line):
            findings.append(
                _finding(
                    path,
                    line_number,
                    "error",
                    "future_only_sections",
                    "completed/pass-history sections belong in the maintenance review record, not TODO.md",
                )
            )
        if _ROTATING_PROJECT.search(line):
            findings.append(
                _finding(
                    path,
                    line_number,
                    "error",
                    "rotating_path",
                    "public backlog must not hard-code private or rotating project paths",
                )
            )

    seen: set[str] = set()
    for identifier in identifiers:
        if identifier in seen:
            findings.append(_finding(path, 1, "error", "duplicate_id", f"duplicate backlog identifier: {identifier}"))
        seen.add(identifier)

    known_names = set(public_names)
    for line_number, line in enumerate(lines, start=1):
        for match in re.findall(r"(?:projects/)?(templates/[A-Za-z0-9_-]+)", line):
            # ``templates/AGENTS`` and similar directory-level contract paths
            # are documentation, not exemplar names.
            if match.rsplit("/", 1)[-1] in {"AGENTS", "README"}:
                continue
            if match not in known_names:
                findings.append(
                    _finding(
                        path,
                        line_number,
                        "warning",
                        "stale_project_name",
                        f"project name is not in public scope: {match}",
                    )
                )

    if not identifiers:
        findings.append(
            _finding(path, 1, "warning", "stable_ids", "backlog has no machine-readable stable identifiers yet")
        )
    if not is_root and not has_backlog_table:
        findings.append(
            _finding(
                path,
                1,
                "error",
                "stable_table",
                "public exemplar backlog must contain the six-field stable backlog table header",
            )
        )
    return findings, tuple(identifiers)


def validate_public_backlogs(
    repo_root: Path | str,
    *,
    public_names: Iterable[str] = PUBLIC_PROJECT_NAMES,
) -> BacklogReport:
    """Validate the root and canonical public exemplar TODO contracts."""
    root = Path(repo_root).resolve()
    names = tuple(public_names)
    paths = public_backlog_paths(root, public_names=names)
    findings: list[BacklogFinding] = []
    identifiers: dict[Path, tuple[str, ...]] = {}
    if not (root / "TO-DO.md").is_file():
        findings.append(_finding(root / "TO-DO.md", 1, "error", "missing_root", "root TO-DO.md is required"))
    present_public = tuple(name for name in names if (root / "projects" / name / "TODO.md").is_file())
    for name in names:
        candidate = root / "projects" / name / "TODO.md"
        if not candidate.is_file():
            findings.append(
                _finding(
                    candidate,
                    1,
                    "error",
                    "missing_exemplar_backlog",
                    f"canonical public exemplar is missing its TODO.md: {name}",
                )
            )
    for path in paths:
        file_findings, file_ids = _validate_file(path, is_root=path == root / "TO-DO.md", public_names=present_public)
        findings.extend(file_findings)
        identifiers[path] = file_ids
    return BacklogReport(files=paths, findings=tuple(findings), identifiers=identifiers)


def format_backlog_report(report: BacklogReport) -> str:
    """Render a stable human-readable backlog report."""
    lines = [
        f"backlog files: {len(report.files)}",
        f"stable identifiers: {sum(len(values) for values in report.identifiers.values())}",
        f"errors: {len(report.errors)}",
        f"warnings: {len(report.warnings)}",
    ]
    for finding in report.findings:
        lines.append(f"{finding.severity.upper()} {finding.path}:{finding.line} [{finding.rule}] {finding.message}")
    return "\n".join(lines)


__all__ = [
    "BacklogFinding",
    "BacklogReport",
    "format_backlog_report",
    "public_backlog_paths",
    "validate_public_backlogs",
]
