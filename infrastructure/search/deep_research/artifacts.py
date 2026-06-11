"""Persistence helpers for deep research reports."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

from infrastructure.core.logging.utils import get_logger
from infrastructure.search.deep_research.models import DeepResearchRequest, DeepResearchResult

logger = get_logger(__name__)


@dataclass(frozen=True)
class DeepResearchReportBundle:
    """Filesystem locations for a saved deep research result."""

    provider: str
    directory: Path
    markdown_path: Path
    json_path: Path
    log_path: Path


def save_deep_research_result(
    project_root: str | Path,
    result: DeepResearchResult,
    *,
    request: DeepResearchRequest | None = None,
    report_name: str | None = None,
) -> DeepResearchReportBundle:
    """Write a single deep research result under ``output/reports/deep_research``."""
    root = Path(project_root).expanduser().resolve()
    directory = root / "output" / "reports" / "deep_research"
    directory.mkdir(parents=True, exist_ok=True)

    base_name = report_name or result.provider
    markdown_path = directory / f"{base_name}.md"
    json_path = directory / f"{base_name}.json"
    log_path = directory / f"{base_name}.log"

    markdown_path.write_text(_format_markdown_report(result, request=request), encoding="utf-8")
    json_path.write_text(_format_json_report(result, request=request), encoding="utf-8")
    log_path.write_text(_format_log_report(result, request=request), encoding="utf-8")

    logger.info("Deep research report saved: %s", markdown_path)
    logger.info("Deep research result JSON saved: %s", json_path)
    logger.info("Deep research log saved: %s", log_path)

    return DeepResearchReportBundle(
        provider=result.provider,
        directory=directory,
        markdown_path=markdown_path,
        json_path=json_path,
        log_path=log_path,
    )


def save_deep_research_results(
    project_root: str | Path,
    results: Mapping[str, DeepResearchResult],
    *,
    request: DeepResearchRequest | None = None,
) -> dict[str, DeepResearchReportBundle]:
    """Write all provider reports and a small index file."""
    bundles: dict[str, DeepResearchReportBundle] = {}
    for provider, result in results.items():
        bundles[provider] = save_deep_research_result(
            project_root,
            result,
            request=request,
            report_name=provider,
        )

    root = Path(project_root).expanduser().resolve()
    index_path = root / "output" / "reports" / "deep_research" / "index.json"
    index_path.write_text(
        json.dumps(
            {
                provider: {
                    "markdown_path": str(bundle.markdown_path),
                    "json_path": str(bundle.json_path),
                    "log_path": str(bundle.log_path),
                }
                for provider, bundle in bundles.items()
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    logger.info("Deep research index saved: %s", index_path)
    return bundles


def _format_markdown_report(result: DeepResearchResult, *, request: DeepResearchRequest | None) -> str:
    lines = [
        "# Deep Research Report",
        "",
        f"- Provider: {result.provider}",
        f"- Job ID: {result.job_id}",
        f"- Status: {result.status}",
    ]
    if request is not None:
        lines.extend(
            [
                f"- Query: {request.query}",
                f"- Output format: {request.output_format}",
                f"- Sections: {', '.join(request.sections)}",
            ]
        )
    lines.extend(["", "## Full Report", ""])
    lines.append(result.output_text.rstrip())
    if result.citations:
        lines.extend(["", "## Citations", ""])
        for citation in result.citations:
            label = citation.title or citation.url or "citation"
            target = citation.url or ""
            lines.append(f"- {label}: {target}".rstrip())
    if result.trace:
        lines.extend(["", "## Trace", ""])
        for item in result.trace:
            lines.append(f"- {item.get('type')}")
    return "\n".join(lines) + "\n"


def _format_json_report(result: DeepResearchResult, *, request: DeepResearchRequest | None) -> str:
    payload = {
        "provider": result.provider,
        "job_id": result.job_id,
        "status": result.status,
        "output_text": result.output_text,
        "citations": [asdict(citation) for citation in result.citations],
        "trace": list(result.trace),
        "raw": result.raw,
    }
    if request is not None:
        payload["request"] = {
            "query": request.query,
            "provider": request.provider,
            "output_format": request.output_format,
            "sections": list(request.sections),
            "instructions": request.instructions,
        }
    return json.dumps(payload, indent=2, default=str) + "\n"


def _format_log_report(result: DeepResearchResult, *, request: DeepResearchRequest | None) -> str:
    lines = [
        "[Deep Research Report]",
        f"provider={result.provider}",
        f"job_id={result.job_id}",
        f"status={result.status}",
    ]
    if request is not None:
        lines.extend(
            [
                f"query={request.query}",
                f"output_format={request.output_format}",
                f"sections={', '.join(request.sections)}",
            ]
        )
    lines.extend(["", result.output_text.rstrip(), ""])
    if result.citations:
        lines.append("[Citations]")
        for citation in result.citations:
            lines.append(
                f"- title={citation.title!r} url={citation.url!r} start={citation.start_index} end={citation.end_index}"
            )
    if result.trace:
        lines.append("[Trace]")
        for item in result.trace:
            lines.append(f"- type={item.get('type')!r}")
    return "\n".join(lines) + "\n"


__all__ = [
    "DeepResearchReportBundle",
    "save_deep_research_result",
    "save_deep_research_results",
]
