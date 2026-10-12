"""CLI for introspecting the declarative pipeline definition.

The pipeline contract is the single source of truth in
``pipeline.yaml`` (see :mod:`infrastructure.core.pipeline.dag`), but until now
that contract was only *re-described in prose* across ``CLAUDE.md``,
``AGENTS.md`` and ``README.md`` — so an agent automating the pipeline had to
either parse YAML itself or trust hand-maintained tables that drift.

This thin CLI derives a machine-readable stage catalog straight from the live
``pipeline.yaml`` (never hand-maintained), so an agent can ask::

    uv run python -m infrastructure.core.pipeline describe-pipeline --format json

and receive, per stage: name, the script or built-in method that runs it, its
tags, whether it is optional (``allow_skip``)/skippable, its ``depends_on``
edges, topological order, declared failure mode, and the contract's
definition-of-done. The default execution view is the same resolved core plan
used by workers; ``--view declared`` shows the entire source declaration.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, TextIO

from infrastructure.core.cli_scaffold import add_schema_flag, emit_schema
from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.dag import PipelineDAG
from infrastructure.core.pipeline.definition import (
    PipelinePurpose,
    PipelineSourceResolutionError,
    resolve_pipeline_source,
)

# Imported rather than restated. Two copies of "which tags are opt-in" drift the
# moment a stage is added: `docxplus_export` was tagged opt-in in
# stage_vocabulary and still counted toward the default full run here, because
# this list had not heard about it.
from infrastructure.core.pipeline.stage_vocabulary import _OPT_IN_TAGS

logger = get_logger(__name__)


@contextmanager
def _preview_logging() -> Iterator[None]:
    """Keep preview diagnostics on stderr and restore their console streams.

    Initialize the genuine script-discovery logger before compilation lazily
    imports it. Only stdout console handlers on the two resolution loggers are
    routed; file/capture handlers, levels, filters and propagation stay intact.
    Ordinary pipeline execution keeps its configured logging outside this scope.
    """
    from infrastructure.core.script_discovery import logger as discovery_logger

    loggers = (logging.getLogger("infrastructure.core.pipeline.dag"), discovery_logger)
    streams: list[tuple[logging.StreamHandler[Any], TextIO]] = []
    for selected in loggers:
        for handler in selected.handlers:
            if (
                isinstance(handler, logging.StreamHandler)
                and not isinstance(handler, logging.FileHandler)
                and (handler.stream is sys.stdout or handler.stream is sys.__stdout__)
                and all(existing is not handler for existing, _stream in streams)
            ):
                streams.append((handler, handler.stream))
    try:
        for handler, _stream in streams:
            handler.setStream(sys.stderr)
        yield
    finally:
        for handler, stream in reversed(streams):
            handler.setStream(stream)


DEFAULT_PIPELINE_YAML = Path(__file__).resolve().parent / "pipeline.yaml"
OPT_IN_STAGE_TAGS = _OPT_IN_TAGS

__all__ = [
    "DEFAULT_PIPELINE_YAML",
    "OPT_IN_STAGE_TAGS",
    "build_parser",
    "describe_pipeline",
    "main",
    "stage_rows",
    "pipeline_description",
]


def _resolve_yaml(args: argparse.Namespace) -> Path:
    """Resolve which pipeline.yaml to read: explicit --yaml, then --project override, then default."""
    raw_repo_root = getattr(args, "repo_root", ".")
    repo_root = Path(raw_repo_root) if isinstance(raw_repo_root, (str, Path)) else Path(".")
    project = getattr(args, "project", None)
    project_root = None
    if isinstance(project, str) and project:
        project_root = repo_root.resolve() / "projects" / project
    return resolve_pipeline_source(
        repo_root,
        project_root,
        explicit_path=getattr(args, "yaml", None),
        purpose=PipelinePurpose.EXECUTION,
    ).path


def stage_rows(
    yaml_path: Path,
    *,
    exclude_tags: set[str] | None = None,
    include_only: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Return one JSON-serializable row per stage, in topological order.

    Args:
        yaml_path: Path to a ``pipeline.yaml``-shaped file.
        exclude_tags: Drop stages carrying any of these tags (e.g. ``{"llm"}``).
        include_only: If given, keep only stages carrying one of these tags.

    Returns:
        A list of dicts derived purely from the YAML — never hand-maintained.

    Resolution diagnostics use stderr within this scope so CLI and MCP callers
    receive clean stdout without discarding the configured logger messages.
    """
    with _preview_logging():
        dag = PipelineDAG.from_yaml(yaml_path)
        if exclude_tags or include_only:
            dag.filter_tags(exclude=exclude_tags or None, include_only=include_only or None)
    rows: list[dict[str, Any]] = []
    for order, stage in enumerate(dag.sorted_stages()):
        contract = stage.contract
        rows.append(
            {
                "order": order,
                "key": stage.key,
                "name": stage.name,
                "runner": stage.script or (f"method:{stage.method}" if stage.method else None),
                "script": stage.script,
                "method": stage.method,
                "args": list(stage.args),
                "tags": list(stage.tags),
                "optional": bool(stage.allow_skip),
                "allow_skip": bool(stage.allow_skip),
                "depends_on": list(stage.depends_on),
                "failure_mode": stage.failure_mode,
                "definition_of_done": getattr(contract, "definition_of_done", "") or "",
                "failure_code": getattr(contract, "failure_code", "") or "",
            }
        )
    return rows


def describe_pipeline(args: argparse.Namespace) -> int:
    """Emit the selected execution contract or explicit declaration catalog."""
    try:
        payload = pipeline_description(
            repo_root=Path(args.repo_root), project=args.project, yaml_path=args.yaml, mode=args.mode, view=args.view
        )
    except (PipelineSourceResolutionError, ValueError, OSError) as exc:
        logger.error("%s", exc)
        return 2
    rows = payload["stages"]

    if args.format == "json":
        sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        return 0

    # table
    sys.stdout.write(f"Pipeline stages ({args.view}, source: {payload['source']}):\n")
    for row in rows:
        opt = " [optional]" if row["optional"] else ""
        tags = ",".join(row["tags"])
        sys.stdout.write(f"  {row['order']:>2}  {row['name']}{opt}  ({tags or 'untagged'}) -> {row['runner']}\n")
    sys.stdout.write(f"{len(rows)} stage(s)\n")
    return 0


def pipeline_description(
    *,
    repo_root: Path,
    project: str | None = None,
    yaml_path: str | Path | None = None,
    mode: str = "core",
    view: str = "execution",
) -> dict[str, Any]:
    """Read-only shared CLI/MCP view; execution resolution creates no output state."""
    from dataclasses import asdict
    from infrastructure.core.pipeline.plan import compile_execution_plan
    from infrastructure.core.pipeline.types import PipelineConfig

    if mode not in {"core", "live"} or view not in {"execution", "declared"}:
        raise ValueError("Use mode core|live and view execution|declared")
    config = PipelineConfig(
        project or "templates/template_code_project",
        repo_root.resolve(),
        mode=mode,
        pipeline_path=Path(yaml_path) if yaml_path else None,
    )
    if view == "declared":
        path = _resolve_yaml(
            argparse.Namespace(repo_root=config.repo_root, project=config.project_name, yaml=yaml_path)
        )
        return {"version": 2, "view": view, "source": str(path), "stages": stage_rows(path)}
    with _preview_logging():
        plan = compile_execution_plan(config)
    rows = [
        {
            "order": i,
            "key": stage.key,
            "name": stage.name,
            "runner": stage.script or f"method:{stage.method}",
            "tags": list(stage.tags),
            "optional": stage.allow_skip,
            "depends_on": list(stage.dependencies),
            "contract": asdict(stage.contract),
        }
        for i, stage in enumerate(plan.stages)
    ]
    return {
        "version": 2,
        "view": view,
        "source": plan.provenance,
        "stages": rows,
        "plan": plan.to_dict(),
        "plan_digest": plan.digest,
    }


def build_parser() -> argparse.ArgumentParser:
    """Create the argparse parser for the pipeline-introspection CLI."""
    parser = argparse.ArgumentParser(
        prog="python -m infrastructure.core.pipeline",
        description="Introspect the declarative pipeline definition (derived from pipeline.yaml).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("describe-pipeline", help="Print the stage catalog derived from pipeline.yaml")
    p.add_argument("--format", choices=["json", "table"], default="json", help="Output format (default: json)")
    p.add_argument("--mode", choices=["core", "live"], default="core")
    p.add_argument("--view", choices=["execution", "declared"], default="execution")
    p.add_argument("--yaml", default=None, help="Explicit pipeline.yaml path (overrides --project and default)")
    p.add_argument("--project", default=None, help="Prefer projects/<name>/pipeline.yaml if it exists")
    p.add_argument("--repo-root", default=".", help="Repository root for --project resolution (default: cwd)")
    add_schema_flag(p)
    p.set_defaults(func=describe_pipeline)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the pipeline-introspection CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "schema", False):
        return emit_schema(parser)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
