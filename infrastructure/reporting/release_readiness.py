"""No-network candidate and published acceptance for the full public roster.

Source-owned profiles and exact artifact snapshots determine acceptance.
Historical COUNTS/pipeline/graph snapshots are informational. Git-ignore reads
reuse the existing public deliverable inventory; no provider is contacted.
The supplied timestamp never participates in acceptance.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from infrastructure.core.logging.utils import get_logger
from infrastructure.reporting import html_templates
from infrastructure.reporting.release_readiness_collectors import (
    _find_newest,
    collect_release_metadata,
    collect_coverage_facts,
    collect_pipeline_state,
    collect_evidence_graph,
    collect_docs_lint,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.reporting.release_readiness_profile import collect_profile
from infrastructure.reporting.release_readiness_types import (
    CoverageFacts,
    DocsLintStatus,
    EvidenceGraphStatus,
    PipelineState,
    ProjectCoverage,
    ReleaseMetadata,
    ReleaseReadinessReport,
)

logger = get_logger(__name__)

# Deterministic default so CLI output is byte-stable without a real clock read.
_DEFAULT_GENERATED_AT = "1970-01-01T00:00:00Z"

_NOT_AVAILABLE = "not available"


# --------------------------------------------------------------------------- #
# Typed sections
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Collectors (local-only, no network / no clock / no git)
# --------------------------------------------------------------------------- #


def collect_release_readiness(
    repo_root: Path,
    *,
    latest_tag: str | None = None,
    docs_lint_json: Path | None = None,
    evidence_graph_filename: str = "evidence_graph.json",
    generated_at: str = _DEFAULT_GENERATED_AT,
    readiness_receipt: Path | None = None,
) -> ReleaseReadinessReport:
    """Observe each artifact once and validate the full required profile offline."""
    repo_root = repo_root.resolve()
    reader = SnapshotReader(repo_root)
    pipeline_path = _find_newest(repo_root, "pipeline_report.json")
    graph_path = _find_newest(repo_root, evidence_graph_filename)
    release = collect_release_metadata(repo_root, latest_tag=latest_tag, reader=reader)
    coverage = collect_coverage_facts(repo_root, reader=reader)
    pipeline = (
        collect_pipeline_state(repo_root, reader=reader, selected=pipeline_path) if pipeline_path else PipelineState()
    )
    graph = (
        collect_evidence_graph(repo_root, reader=reader, selected=graph_path) if graph_path else EvidenceGraphStatus()
    )
    docs = collect_docs_lint(docs_lint_json, reader=reader)
    evidence = collect_profile(repo_root, readiness_receipt, reader)
    return ReleaseReadinessReport(generated_at, release, coverage, pipeline, graph, docs, evidence)


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
    lines.append(f"**Overall**: {_verdict(report.overall_ready)} ({report.status})")
    lines.append(f"**Candidate acceptance**: {report.evidence.candidate_state}")
    lines.append(f"**Released acceptance**: {report.evidence.released_state}")
    lines.append(
        f"**Preparation allowed**: {'yes' if report.candidate_ready else 'no'}; production approval remains required."
    )
    lines.append("Local evidence validation; execution and remote provenance remain the producer's responsibility.")
    if report.evidence.issues:
        lines.append("")
        lines.extend(f"- Evidence: {issue}" for issue in report.evidence.issues[:20])
        if len(report.evidence.issues) > 20:
            lines.append(
                f"- {len(report.evidence.issues) - 20} additional required gates are unresolved; see JSON evidence."
            )
    lines.append("")

    # Release metadata
    lines.append("## Release Metadata")
    lines.append("")
    rel = report.release
    lines.append(f"- **Version**: {rel.version if rel.version else _NOT_AVAILABLE}")
    lines.append(f"- **Unverified tag hint**: {rel.latest_tag if rel.latest_tag else _NOT_AVAILABLE}")
    lines.append(f"- **Verified published tag**: {report.evidence.verified_tag or _NOT_AVAILABLE}")
    lines.append(f"- **Verified published version**: {report.evidence.published_version or _NOT_AVAILABLE}")
    lines.append(
        f"- **Changelog version**: {rel.latest_changelog_version if rel.latest_changelog_version else _NOT_AVAILABLE}"
    )
    lines.append("")

    # Pipeline state
    lines.append("## Pipeline State")
    lines.append("")
    pipe = report.pipeline
    if pipe.available:
        lines.append("- **Status**: informational snapshot; full roster completion requires the bound execution plans")
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
        {"title": "Overall", "value": f"{_verdict(report.overall_ready)} ({report.status})"},
        {"title": "Candidate acceptance", "value": report.evidence.candidate_state},
        {"title": "Released acceptance", "value": report.evidence.released_state},
        {"title": "Version", "value": rel.version if rel.version else _NOT_AVAILABLE},
        {
            "title": "Pipeline",
            "value": "informational snapshot" if report.pipeline.available else _NOT_AVAILABLE,
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
                    ["Status", "informational snapshot"],
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
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return 0/pass, 1/fail, 75/blocked, or 2/unknown for the selected profile.",
    )
    parser.add_argument(
        "--profile",
        choices=["candidate", "released"],
        default="released",
        help="Required acceptance profile (default: released).",
    )
    parser.add_argument("--readiness-receipt", type=Path, help="Source and artifact receipt from executed checks.")
    parser.add_argument("--out", type=Path, default=None, help="Output file path; prints to stdout if omitted.")
    parser.add_argument(
        "--format",
        choices=["markdown", "html", "json"],
        default="markdown",
        help="Output format (default: markdown).",
    )
    parser.add_argument(
        "--latest-tag",
        default=None,
        help="Informational, unverified tag hint; cannot grant published acceptance.",
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
        readiness_receipt=args.readiness_receipt,
    )

    content = (
        json.dumps(report.to_dict(), sort_keys=True, indent=2)
        if args.format == "json"
        else render_html(report)
        if args.format == "html"
        else render_markdown(report)
    )

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(content, encoding="utf-8")
        logger.info("Release-readiness report written: %s", args.out)
    else:
        sys.stdout.write(content + "\n")
    state = report.evidence.candidate_state if args.profile == "candidate" else report.evidence.released_state
    return {"pass": 0, "fail": 1, "blocked": 75, "unknown": 2}[state] if args.strict else 0


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
