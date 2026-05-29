"""Doctor detectors — Repository layout checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any


from infrastructure.doctor.models import Finding, Severity


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
