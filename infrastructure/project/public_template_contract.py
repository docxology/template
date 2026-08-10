"""Fail-closed structural contracts for the canonical public exemplars.

The public roster is a release surface, not merely a discovery hint. This
module checks the on-disk shape of every declared exemplar without importing
project code, running project scripts, following private symlinks, or making
network calls. The report is small enough to run before the isolated project
matrix.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES

REQUIRED_MARKERS: tuple[str, ...] = ("AGENTS.md", "README.md", "TODO.md", "pyproject.toml")
REQUIRED_DIRECTORIES: tuple[str, ...] = ("src", "tests")


@dataclass(frozen=True)
class PublicTemplateFinding:
    """One structural finding for a public exemplar."""

    project: str
    code: str
    message: str


@dataclass(frozen=True)
class PublicTemplateContractReport:
    """Roster-wide result for the public exemplar contract."""

    projects: tuple[str, ...]
    findings: tuple[PublicTemplateFinding, ...]

    @property
    def passed(self) -> bool:
        """Whether every declared public exemplar satisfies the contract."""
        return not self.findings

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-safe report."""
        return {
            "schema_version": "template-public-contract/v1",
            "status": "pass" if self.passed else "fail",
            "project_count": len(self.projects),
            "projects": list(self.projects),
            "findings": [
                {"project": item.project, "code": item.code, "message": item.message} for item in self.findings
            ],
        }


def _test_files(path: Path) -> tuple[Path, ...]:
    """Return ordinary project test files without traversing symlinked dirs."""
    return tuple(sorted(item for item in path.glob("test_*.py") if item.is_file() and not item.is_symlink()))


def validate_public_template_contract(
    repo_root: Path | str,
    *,
    public_names: Iterable[str] = PUBLIC_PROJECT_NAMES,
) -> PublicTemplateContractReport:
    """Validate every canonical public exemplar's non-empty fork surface."""
    root = Path(repo_root).resolve()
    projects = tuple(sorted(public_names))
    findings: list[PublicTemplateFinding] = []
    for project in projects:
        project_root = root / "projects" / project
        if not project_root.exists():
            findings.append(PublicTemplateFinding(project, "MISSING-ROOT", "public exemplar directory is missing"))
            continue
        if project_root.is_symlink():
            findings.append(
                PublicTemplateFinding(project, "SYMLINK-ROOT", "public exemplar root must not be a symlink")
            )
            continue
        for marker in REQUIRED_MARKERS:
            marker_path = project_root / marker
            if not marker_path.is_file() or marker_path.is_symlink():
                findings.append(PublicTemplateFinding(project, "MISSING-MARKER", f"missing regular marker: {marker}"))
        for directory in REQUIRED_DIRECTORIES:
            directory_path = project_root / directory
            if not directory_path.is_dir() or directory_path.is_symlink():
                findings.append(
                    PublicTemplateFinding(project, "MISSING-DIRECTORY", f"missing regular directory: {directory}")
                )
        src_files = tuple(item for item in (project_root / "src").rglob("*.py") if item.is_file())
        if not src_files:
            findings.append(PublicTemplateFinding(project, "EMPTY-SOURCE", "src contains no Python source files"))
        test_files = _test_files(project_root / "tests")
        if not test_files:
            findings.append(
                PublicTemplateFinding(project, "EMPTY-TEST-SCOPE", "tests contains no top-level test_*.py files")
            )
    return PublicTemplateContractReport(projects, tuple(findings))


def format_public_template_contract(report: PublicTemplateContractReport) -> str:
    """Render a compact human-readable contract report."""
    lines = [
        f"public exemplars: {len(report.projects)}",
        f"status: {'pass' if report.passed else 'fail'}",
        f"findings: {len(report.findings)}",
    ]
    lines.extend(f"{item.project}: {item.code}: {item.message}" for item in report.findings)
    return "\n".join(lines)


__all__ = [
    "PublicTemplateContractReport",
    "PublicTemplateFinding",
    "format_public_template_contract",
    "validate_public_template_contract",
]
