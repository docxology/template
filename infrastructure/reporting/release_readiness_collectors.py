"""Informational local snapshots; acceptance authority comes from the required profile."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from typing import Any

from infrastructure.core.files.serialization import relative_or_self as _rel
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.release_readiness_types import (
    CoverageFacts,
    DocsLintStatus,
    EvidenceGraphStatus,
    PipelineState,
    ProjectCoverage,
    ReleaseMetadata,
)


def _read_text(path: Path, reader: SnapshotReader | None) -> str | None:
    try:
        if reader is None:
            return path.read_text(encoding="utf-8")
        return reader.read(path.absolute().relative_to(reader.root).as_posix()).content.decode("utf-8")
    except (OSError, ValueError, UnicodeError):
        return None


def _read_json(path: Path, reader: SnapshotReader | None = None) -> dict[str, Any] | None:
    try:
        data = json.loads(_read_text(path, reader) or "")
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def collect_release_metadata(
    repo_root: Path, *, latest_tag: str | None = None, reader: SnapshotReader | None = None
) -> ReleaseMetadata:
    """Read version from pyproject.toml and a tag hint from CHANGELOG.md."""
    version: str | None = None
    source: str | None = None
    pyproject = repo_root / "pyproject.toml"
    if pyproject.is_file():
        try:
            data = tomllib.loads(_read_text(pyproject, reader) or "")
            project = data.get("project")
            raw = project.get("version") if isinstance(project, dict) else None
            if isinstance(raw, str):
                version = raw
                source = _rel(pyproject, repo_root)
        except (OSError, tomllib.TOMLDecodeError):
            version = None

    changelog_version = _latest_changelog_version(repo_root, reader)
    return ReleaseMetadata(
        version=version,
        latest_tag=latest_tag,
        latest_changelog_version=changelog_version,
        source=source,
    )


def _latest_changelog_version(repo_root: Path, reader: SnapshotReader | None = None) -> str | None:
    """Return the first non-Unreleased ``## [x.y.z]`` heading in CHANGELOG.md."""
    changelog = repo_root / "CHANGELOG.md"
    if not changelog.is_file():
        return None
    try:
        text = _read_text(changelog, reader) or ""
    except OSError:
        return None
    for match in re.finditer(r"^##\s*\[([^\]]+)\]", text, flags=re.MULTILINE):
        token = match.group(1).strip()
        if token.lower() == "unreleased":
            continue
        return token
    return None


# Matches COUNTS.md coverage rows: | `name` | 196 | 98.25 % |
_COVERAGE_ROW = re.compile(
    r"^\|\s*`(?P<name>[^`]+)`\s*\|\s*(?P<tests>[\d,]+)\s*\|\s*(?P<cov>[\d.]+)\s*%\s*\|",
    flags=re.MULTILINE,
)


def collect_coverage_facts(repo_root: Path, *, reader: SnapshotReader | None = None) -> CoverageFacts:
    """Parse the per-project coverage table from COUNTS.md."""
    facts = repo_root / "docs" / "_generated" / "COUNTS.md"
    if not facts.is_file():
        return CoverageFacts(available=False)
    try:
        text = _read_text(facts, reader) or ""
    except OSError:
        return CoverageFacts(available=False)

    projects: list[ProjectCoverage] = []
    for match in _COVERAGE_ROW.finditer(text):
        name = match.group("name").strip()
        try:
            tests: int | None = int(match.group("tests").replace(",", ""))
        except ValueError:
            tests = None
        try:
            cov: float | None = float(match.group("cov"))
        except ValueError:
            cov = None
        projects.append(ProjectCoverage(name=name, tests=tests, coverage_percent=cov))

    # Deterministic ordering regardless of source row order.
    projects.sort(key=lambda p: p.name)
    return CoverageFacts(
        available=bool(projects),
        projects=projects,
        source=_rel(facts, repo_root) if projects else None,
    )


def _find_newest(repo_root: Path, filename: str) -> Path | None:
    """Return the newest public ``output/**/reports/<filename>`` by mtime.

    Falls back to lexicographic path ordering when mtimes tie, so selection is
    deterministic across filesystems.
    """
    output = repo_root / "output"
    if not output.is_dir():
        return None
    candidates: list[Path] = []
    for qualified in PUBLIC_PROJECT_NAMES:
        for base in (output / qualified, output / qualified.split("/")[-1]):
            if not base.is_dir() or base.is_symlink():
                continue
            candidates.extend(
                path
                for path in base.glob(f"**/reports/{filename}")
                if path.is_file()
                and not path.is_symlink()
                and not any(parent.is_symlink() for parent in path.parents if parent != repo_root)
            )
    if not candidates:
        return None
    observed: list[tuple[float, str, Path]] = []
    for candidate in candidates:
        try:
            observed.append((candidate.stat().st_mtime, str(candidate), candidate))
        except OSError:
            continue
    return max(observed)[2] if observed else None


def collect_pipeline_state(
    repo_root: Path, *, reader: SnapshotReader | None = None, selected: Path | None = None
) -> PipelineState:
    """Summarize the newest pipeline_report.json snapshot under output/."""
    snapshot = selected if selected is not None else _find_newest(repo_root, "pipeline_report.json")
    if snapshot is None:
        return PipelineState(available=False)
    data = _read_json(snapshot, reader)
    if data is None:
        return PipelineState(available=False)

    stages = data.get("stages", [])
    if not isinstance(stages, list):
        stages = []
    passed = sum(
        1
        for stage in stages
        if isinstance(stage, dict)
        and type(stage.get("exit_code")) is int
        and stage["exit_code"] == 0
        and stage.get("status") == "passed"
    )
    failed = len(stages) - passed
    duration = data.get("total_duration")
    return PipelineState(
        available=True,
        source=_rel(snapshot, repo_root),
        total_stages=len(stages),
        passed_stages=passed,
        failed_stages=failed,
        total_duration=float(duration) if isinstance(duration, (int, float)) else None,
    )


def collect_evidence_graph(
    repo_root: Path,
    *,
    filename: str = "evidence_graph.json",
    reader: SnapshotReader | None = None,
    selected: Path | None = None,
) -> EvidenceGraphStatus:
    """Report evidence-graph status from a local JSON file under output/."""
    snapshot = selected if selected is not None else _find_newest(repo_root, filename)
    if snapshot is None:
        return EvidenceGraphStatus(available=False)
    data = _read_json(snapshot, reader)
    if data is None:
        return EvidenceGraphStatus(available=False)

    nodes = data.get("nodes")
    edges = data.get("edges")
    node_count = len(nodes) if isinstance(nodes, list) else None
    edge_count = len(edges) if isinstance(edges, list) else None
    return EvidenceGraphStatus(
        available=True,
        source=_rel(snapshot, repo_root),
        node_count=node_count,
        edge_count=edge_count,
    )


def collect_docs_lint(docs_lint_json: Path | None, *, reader: SnapshotReader | None = None) -> DocsLintStatus:
    """Summarize a docs-lint JSON snapshot (lint_runner --json shape)."""
    if docs_lint_json is None or not docs_lint_json.is_file():
        return DocsLintStatus(available=False)
    data = _read_json(docs_lint_json, reader)
    if data is None:
        return DocsLintStatus(available=False)

    def _count(key: str) -> int:
        value = data.get(key)
        return len(value) if isinstance(value, list) else 0

    return DocsLintStatus(
        available=True,
        source=str(docs_lint_json),
        mermaid=_count("mermaid"),
        broken_links=_count("broken_links"),
        consistency=_count("consistency"),
        doc_pairs=_count("doc_pairs"),
        valid=all(isinstance(data.get(key), list) for key in ("mermaid", "broken_links", "consistency", "doc_pairs")),
    )
