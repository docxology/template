"""Local, no-network release-readiness dashboard.

Consolidates a single release-readiness view from artifacts that *already* exist
on disk — no network calls, no git invocation, no wall-clock reads. Every input
is a local JSON/Markdown file produced by the rest of the pipeline:

* **Docs lint** — the JSON payload of ``scripts/audit/lint_docs.py --json`` (the shape
  emitted by :func:`infrastructure.validation.docs.lint_runner.emit_json_report`),
  passed as a file path via ``docs_lint_json``.
* **Coverage / test facts** — parsed from ``docs/_generated/COUNTS.md``.
* **Pipeline state** — the newest ``output/**/reports/pipeline_report.json``
  snapshot (the shape written by
  :func:`infrastructure.reporting.pipeline_io.save_pipeline_report`).
* **Evidence-graph status** — an ``evidence_graph.json`` under ``output/**`` if
  present; otherwise reported as not generated.
* **Release metadata** — ``pyproject.toml`` version, plus a ``latest_tag`` accepted
  as a parameter or read from ``CHANGELOG.md`` (never via git).

Outputs a typed :class:`ReleaseReadinessReport`, deterministic Markdown, and a
static HTML page that reuses :mod:`infrastructure.reporting.html_templates`.

The module never reads the clock: a ``generated_at`` timestamp must be supplied
by the caller (the CLI defaults it to a fixed, deterministic placeholder so that
generated artifacts stay byte-stable in tests and CI).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:  # Python <3.11 — use backport
    import tomli as tomllib  # type: ignore[no-redef]

from infrastructure.core.files.serialization import relative_or_self as _rel
from infrastructure.core.logging.utils import get_logger
from infrastructure.reporting import html_templates

logger = get_logger(__name__)

# Deterministic default so CLI output is byte-stable without a real clock read.
_DEFAULT_GENERATED_AT = "1970-01-01T00:00:00Z"

_NOT_AVAILABLE = "not available"


# --------------------------------------------------------------------------- #
# Typed sections
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ReleaseMetadata:
    """Version and tag facts read from local files only."""

    version: str | None = None
    latest_tag: str | None = None
    latest_changelog_version: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class ProjectCoverage:
    """A single project's collected-test and coverage facts."""

    name: str
    tests: int | None
    coverage_percent: float | None


@dataclass(frozen=True)
class CoverageFacts:
    """Coverage/test facts parsed from COUNTS.md."""

    available: bool = False
    projects: list[ProjectCoverage] = field(default_factory=list)
    source: str | None = None


@dataclass(frozen=True)
class PipelineState:
    """Newest pipeline-report snapshot, if any."""

    available: bool = False
    source: str | None = None
    total_stages: int = 0
    passed_stages: int = 0
    failed_stages: int = 0
    total_duration: float | None = None

    @property
    def ready(self) -> bool:
        """Return True if the artifact is ready for publication."""
        return self.available and self.failed_stages == 0 and self.total_stages > 0


@dataclass(frozen=True)
class EvidenceGraphStatus:
    """Evidence-graph generation status."""

    available: bool = False
    source: str | None = None
    node_count: int | None = None
    edge_count: int | None = None


@dataclass(frozen=True)
class DocsLintStatus:
    """Documentation-lint status from a JSON snapshot."""

    available: bool = False
    source: str | None = None
    mermaid: int = 0
    broken_links: int = 0
    consistency: int = 0
    doc_pairs: int = 0

    @property
    def total_issues(self) -> int:
        """Return the total number of issues across all categories."""
        return self.mermaid + self.broken_links + self.consistency + self.doc_pairs

    @property
    def ready(self) -> bool:
        """Return True if the artifact is ready for publication."""
        return self.available and self.total_issues == 0


@dataclass(frozen=True)
class ReleaseReadinessReport:
    """Consolidated, typed release-readiness view."""

    generated_at: str
    release: ReleaseMetadata
    coverage: CoverageFacts
    pipeline: PipelineState
    evidence_graph: EvidenceGraphStatus
    docs_lint: DocsLintStatus

    @property
    def overall_ready(self) -> bool:
        """True only when every *available* gate is green.

        Absent inputs do not block readiness (they render as "not available"),
        but any present gate that is failing flips the overall verdict.
        """
        if self.pipeline.available and not self.pipeline.ready:
            return False
        if self.docs_lint.available and not self.docs_lint.ready:
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        """Return a plain, JSON-serializable dict (byte-stable with sort_keys)."""
        return {
            "generated_at": self.generated_at,
            "overall_ready": self.overall_ready,
            "release": asdict(self.release),
            "coverage": {
                "available": self.coverage.available,
                "source": self.coverage.source,
                "projects": [asdict(p) for p in self.coverage.projects],
            },
            "pipeline": {**asdict(self.pipeline), "ready": self.pipeline.ready},
            "evidence_graph": asdict(self.evidence_graph),
            "docs_lint": {
                **asdict(self.docs_lint),
                "total_issues": self.docs_lint.total_issues,
                "ready": self.docs_lint.ready,
            },
        }


# --------------------------------------------------------------------------- #
# Collectors (local-only, no network / no clock / no git)
# --------------------------------------------------------------------------- #


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def collect_release_metadata(repo_root: Path, *, latest_tag: str | None = None) -> ReleaseMetadata:
    """Read version from pyproject.toml and a tag hint from CHANGELOG.md."""
    version: str | None = None
    source: str | None = None
    pyproject = repo_root / "pyproject.toml"
    if pyproject.is_file():
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            raw = data.get("project", {}).get("version")
            if isinstance(raw, str):
                version = raw
                source = _rel(pyproject, repo_root)
        except (OSError, tomllib.TOMLDecodeError):
            version = None

    changelog_version = _latest_changelog_version(repo_root)
    return ReleaseMetadata(
        version=version,
        latest_tag=latest_tag if latest_tag else changelog_version,
        latest_changelog_version=changelog_version,
        source=source,
    )


def _latest_changelog_version(repo_root: Path) -> str | None:
    """Return the first non-Unreleased ``## [x.y.z]`` heading in CHANGELOG.md."""
    changelog = repo_root / "CHANGELOG.md"
    if not changelog.is_file():
        return None
    try:
        text = changelog.read_text(encoding="utf-8")
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


def collect_coverage_facts(repo_root: Path) -> CoverageFacts:
    """Parse the per-project coverage table from COUNTS.md."""
    facts = repo_root / "docs" / "_generated" / "COUNTS.md"
    if not facts.is_file():
        return CoverageFacts(available=False)
    try:
        text = facts.read_text(encoding="utf-8")
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
    """Return the newest matching ``output/**/reports/<filename>`` by mtime.

    Falls back to lexicographic path ordering when mtimes tie, so selection is
    deterministic across filesystems.
    """
    output = repo_root / "output"
    if not output.is_dir():
        return None
    candidates = sorted(output.glob(f"**/reports/{filename}"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: (p.stat().st_mtime, str(p)))


def collect_pipeline_state(repo_root: Path) -> PipelineState:
    """Summarize the newest pipeline_report.json snapshot under output/."""
    snapshot = _find_newest(repo_root, "pipeline_report.json")
    if snapshot is None:
        return PipelineState(available=False)
    data = _read_json(snapshot)
    if data is None:
        return PipelineState(available=False)

    stages = data.get("stages", [])
    if not isinstance(stages, list):
        stages = []
    passed = sum(1 for s in stages if isinstance(s, dict) and s.get("exit_code", 1) == 0)
    failed = sum(1 for s in stages if isinstance(s, dict) and s.get("exit_code", 1) != 0)
    duration = data.get("total_duration")
    return PipelineState(
        available=True,
        source=_rel(snapshot, repo_root),
        total_stages=len(stages),
        passed_stages=passed,
        failed_stages=failed,
        total_duration=float(duration) if isinstance(duration, (int, float)) else None,
    )


def collect_evidence_graph(repo_root: Path, *, filename: str = "evidence_graph.json") -> EvidenceGraphStatus:
    """Report evidence-graph status from a local JSON file under output/."""
    snapshot = _find_newest(repo_root, filename)
    if snapshot is None:
        return EvidenceGraphStatus(available=False)
    data = _read_json(snapshot)
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


def collect_docs_lint(docs_lint_json: Path | None) -> DocsLintStatus:
    """Summarize a docs-lint JSON snapshot (lint_runner --json shape)."""
    if docs_lint_json is None or not docs_lint_json.is_file():
        return DocsLintStatus(available=False)
    data = _read_json(docs_lint_json)
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
    )


def collect_release_readiness(
    repo_root: Path,
    *,
    latest_tag: str | None = None,
    docs_lint_json: Path | None = None,
    evidence_graph_filename: str = "evidence_graph.json",
    generated_at: str = _DEFAULT_GENERATED_AT,
) -> ReleaseReadinessReport:
    """Aggregate every local artifact into a typed report. No network, no clock, no git."""
    return ReleaseReadinessReport(
        generated_at=generated_at,
        release=collect_release_metadata(repo_root, latest_tag=latest_tag),
        coverage=collect_coverage_facts(repo_root),
        pipeline=collect_pipeline_state(repo_root),
        evidence_graph=collect_evidence_graph(repo_root, filename=evidence_graph_filename),
        docs_lint=collect_docs_lint(docs_lint_json),
    )


# --------------------------------------------------------------------------- #
# Renderers
# --------------------------------------------------------------------------- #


def _verdict(ready: bool) -> str:
    return "READY" if ready else "NOT READY"


def render_markdown(report: ReleaseReadinessReport) -> str:
    """Render a deterministic Markdown release-readiness dashboard."""
    lines: list[str] = []
    lines.append("# Release Readiness")
    lines.append("")
    lines.append(f"**Generated**: {report.generated_at}")
    lines.append(f"**Overall**: {_verdict(report.overall_ready)}")
    lines.append("")

    # Release metadata
    lines.append("## Release Metadata")
    lines.append("")
    rel = report.release
    lines.append(f"- **Version**: {rel.version if rel.version else _NOT_AVAILABLE}")
    lines.append(f"- **Latest tag**: {rel.latest_tag if rel.latest_tag else _NOT_AVAILABLE}")
    lines.append(
        f"- **Changelog version**: {rel.latest_changelog_version if rel.latest_changelog_version else _NOT_AVAILABLE}"
    )
    lines.append("")

    # Pipeline state
    lines.append("## Pipeline State")
    lines.append("")
    pipe = report.pipeline
    if pipe.available:
        lines.append(f"- **Status**: {_verdict(pipe.ready)}")
        lines.append(f"- **Stages**: {pipe.passed_stages} passed / {pipe.failed_stages} failed of {pipe.total_stages}")
        if pipe.total_duration is not None:
            lines.append(f"- **Duration**: {pipe.total_duration:.1f}s")
        lines.append(f"- **Source**: `{pipe.source}`")
    else:
        lines.append(f"Pipeline snapshot {_NOT_AVAILABLE} (no `output/**/reports/pipeline_report.json`).")
    lines.append("")

    # Coverage / test facts
    lines.append("## Coverage & Test Facts")
    lines.append("")
    cov = report.coverage
    if cov.available:
        lines.append("| Project | Tests | Coverage |")
        lines.append("| --- | --- | --- |")
        for proj in cov.projects:
            tests = f"{proj.tests:,}" if proj.tests is not None else _NOT_AVAILABLE
            pct = f"{proj.coverage_percent:.2f}%" if proj.coverage_percent is not None else _NOT_AVAILABLE
            lines.append(f"| `{proj.name}` | {tests} | {pct} |")
        lines.append("")
        lines.append(f"Source: `{cov.source}`")
    else:
        lines.append(f"Coverage facts {_NOT_AVAILABLE} (no `docs/_generated/COUNTS.md`).")
    lines.append("")

    # Evidence graph
    lines.append("## Evidence Graph")
    lines.append("")
    eg = report.evidence_graph
    if eg.available:
        nodes = eg.node_count if eg.node_count is not None else _NOT_AVAILABLE
        edges = eg.edge_count if eg.edge_count is not None else _NOT_AVAILABLE
        lines.append("- **Status**: generated")
        lines.append(f"- **Nodes**: {nodes}")
        lines.append(f"- **Edges**: {edges}")
        lines.append(f"- **Source**: `{eg.source}`")
    else:
        lines.append(f"Evidence graph {_NOT_AVAILABLE} (not generated).")
    lines.append("")

    # Docs lint
    lines.append("## Documentation Lint")
    lines.append("")
    docs = report.docs_lint
    if docs.available:
        lines.append(f"- **Status**: {_verdict(docs.ready)}")
        lines.append(f"- **Total issues**: {docs.total_issues}")
        lines.append(
            f"- **Breakdown**: mermaid {docs.mermaid}, links {docs.broken_links}, "
            f"consistency {docs.consistency}, doc-pairs {docs.doc_pairs}"
        )
    else:
        lines.append(f"Docs-lint snapshot {_NOT_AVAILABLE} (pass `--docs-lint-json`).")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Report generated by `infrastructure.reporting.release_readiness`*")
    return "\n".join(lines)


def render_html(report: ReleaseReadinessReport) -> str:
    """Render a static HTML dashboard reusing the shared reporting templates."""
    rel = report.release
    cards = [
        {"title": "Overall", "value": _verdict(report.overall_ready)},
        {"title": "Version", "value": rel.version if rel.version else _NOT_AVAILABLE},
        {
            "title": "Pipeline",
            "value": _verdict(report.pipeline.ready) if report.pipeline.available else _NOT_AVAILABLE,
        },
        {
            "title": "Docs Lint",
            "value": _verdict(report.docs_lint.ready) if report.docs_lint.available else _NOT_AVAILABLE,
        },
    ]

    sections: list[str] = []
    sections.append('<div class="section"><h2>Summary</h2>')
    sections.append(html_templates.render_summary_cards(cards))
    sections.append("</div>")

    # Coverage table
    sections.append('<div class="section"><h2>Coverage &amp; Test Facts</h2>')
    if report.coverage.available:
        rows = [
            [
                p.name,
                f"{p.tests:,}" if p.tests is not None else _NOT_AVAILABLE,
                f"{p.coverage_percent:.2f}%" if p.coverage_percent is not None else _NOT_AVAILABLE,
            ]
            for p in report.coverage.projects
        ]
        sections.append(html_templates.render_table(["Project", "Tests", "Coverage"], rows))
    else:
        sections.append(f"<p>Coverage facts {_NOT_AVAILABLE}.</p>")
    sections.append("</div>")

    # Pipeline table
    sections.append('<div class="section"><h2>Pipeline State</h2>')
    pipe = report.pipeline
    if pipe.available:
        sections.append(
            html_templates.render_table(
                ["Metric", "Value"],
                [
                    ["Status", _verdict(pipe.ready)],
                    ["Stages", f"{pipe.passed_stages} passed / {pipe.failed_stages} failed of {pipe.total_stages}"],
                    ["Source", str(pipe.source)],
                ],
            )
        )
    else:
        sections.append(f"<p>Pipeline snapshot {_NOT_AVAILABLE}.</p>")
    sections.append("</div>")

    header = f'<div class="header"><h1>Release Readiness</h1><p>Generated: {report.generated_at}</p></div>'
    footer = '<div class="footer">Generated by <code>infrastructure.reporting.release_readiness</code></div>'
    return html_templates.get_base_html_template().format(
        title="Release Readiness",
        header=header,
        content="\n".join(sections),
        footer=footer,
    )


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m infrastructure.reporting.release_readiness",
        description="Generate a local, no-network release-readiness dashboard from existing artifacts.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root (defaults to the template root).",
    )
    parser.add_argument("--out", type=Path, default=None, help="Output file path; prints to stdout if omitted.")
    parser.add_argument(
        "--format",
        choices=["markdown", "html"],
        default="markdown",
        help="Output format (default: markdown).",
    )
    parser.add_argument(
        "--latest-tag",
        default=None,
        help="Latest release tag (no git is called). Falls back to the newest CHANGELOG.md version.",
    )
    parser.add_argument(
        "--docs-lint-json",
        type=Path,
        default=None,
        help="Path to a `scripts/audit/lint_docs.py --json` snapshot to fold in.",
    )
    parser.add_argument(
        "--generated-at",
        default=_DEFAULT_GENERATED_AT,
        help="Timestamp to stamp into the report (no clock is read).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns 0 on success."""
    args = _build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()

    report = collect_release_readiness(
        repo_root,
        latest_tag=args.latest_tag,
        docs_lint_json=args.docs_lint_json,
        generated_at=args.generated_at,
    )

    content = render_html(report) if args.format == "html" else render_markdown(report)

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(content, encoding="utf-8")
        logger.info("Release-readiness report written: %s", args.out)
    else:
        sys.stdout.write(content + "\n")
    return 0


__all__ = [
    "CoverageFacts",
    "DocsLintStatus",
    "EvidenceGraphStatus",
    "PipelineState",
    "ProjectCoverage",
    "ReleaseMetadata",
    "ReleaseReadinessReport",
    "collect_coverage_facts",
    "collect_docs_lint",
    "collect_evidence_graph",
    "collect_pipeline_state",
    "collect_release_metadata",
    "collect_release_readiness",
    "main",
    "render_html",
    "render_markdown",
]


if __name__ == "__main__":
    raise SystemExit(main())
