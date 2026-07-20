"""CLI for introspecting the declarative pipeline definition.

The 14-stage pipeline contract is the single source of truth in
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
definition-of-done. ``--core-only`` mirrors the pipeline executor's core path.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from infrastructure.core.cli_scaffold import add_schema_flag, emit_schema
from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pipeline.dag import PipelineDAG
from infrastructure.core.pipeline.definition import (
    PipelinePurpose,
    PipelineSourceResolutionError,
    resolve_pipeline_source,
)

logger = get_logger(__name__)


@contextmanager
def _quiet_dag_logging() -> Iterator[None]:
    """Silence the dag loader's INFO line so JSON/table output to stdout stays clean.

    ``PipelineDAG.from_yaml`` emits an INFO log that the project's logging config
    routes to stdout; for a machine-readable catalog command that would corrupt
    the JSON stream. Raise the dag logger to WARNING for the duration.
    """
    dag_logger = logging.getLogger("infrastructure.core.pipeline.dag")
    previous = dag_logger.level
    dag_logger.setLevel(logging.WARNING)
    try:
        yield
    finally:
        dag_logger.setLevel(previous)


DEFAULT_PIPELINE_YAML = Path(__file__).resolve().parent / "pipeline.yaml"
OPT_IN_STAGE_TAGS = frozenset({"ebook", "metadata", "bundle", "archival", "science", "provenance"})
CORE_ONLY_EXCLUDED_TAGS = frozenset({"llm", *OPT_IN_STAGE_TAGS})

__all__ = [
    "CORE_ONLY_EXCLUDED_TAGS",
    "DEFAULT_PIPELINE_YAML",
    "OPT_IN_STAGE_TAGS",
    "build_parser",
    "describe_pipeline",
    "main",
    "stage_rows",
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

    The DAG loader logs to stdout; this function silences that for the duration
    so every caller (CLI ``--format json`` AND the MCP ``describe_pipeline`` tool)
    gets a clean stream without each having to remember the guard.
    """
    with _quiet_dag_logging():
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
    """Emit the derived stage catalog as JSON or a human-readable table."""
    try:
        yaml_path = _resolve_yaml(args)
    except PipelineSourceResolutionError as exc:
        logger.error("%s", exc)
        return 1
    if not yaml_path.is_file():
        logger.error("pipeline.yaml not found: %s", yaml_path)
        return 1

    exclude = set(CORE_ONLY_EXCLUDED_TAGS) if getattr(args, "core_only", False) else None
    rows = stage_rows(yaml_path, exclude_tags=exclude)  # stage_rows quiets dag logging internally

    if args.format == "json":
        payload = {"version": 1, "source": yaml_path.as_posix(), "stages": rows}
        sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        return 0

    # table
    sys.stdout.write(f"Pipeline stages (source: {yaml_path}):\n")
    for row in rows:
        opt = " [optional]" if row["optional"] else ""
        tags = ",".join(row["tags"])
        sys.stdout.write(f"  {row['order']:>2}  {row['name']}{opt}  ({tags or 'untagged'}) -> {row['runner']}\n")
    sys.stdout.write(f"{len(rows)} stage(s)\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Create the argparse parser for the pipeline-introspection CLI."""
    parser = argparse.ArgumentParser(
        prog="python -m infrastructure.core.pipeline",
        description="Introspect the declarative pipeline definition (derived from pipeline.yaml).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("describe-pipeline", help="Print the stage catalog derived from pipeline.yaml")
    p.add_argument("--format", choices=["json", "table"], default="json", help="Output format (default: json)")
    p.add_argument(
        "--core-only",
        action="store_true",
        help="Exclude LLM-tagged and opt-in publishing/archive stages (mirrors --core-only runs)",
    )
    p.add_argument("--yaml", default=None, help="Explicit pipeline.yaml path (overrides --project and default)")
    p.add_argument("--project", default=None, help="Prefer projects/<name>/pipeline.yaml if it exists")
    p.add_argument("--repo-root", default=".", help="Repository root for --project resolution (default: cwd)")
    add_schema_flag(p)
    p.set_defaults(func=describe_pipeline)

    # Alias: list-stages == describe-pipeline (common agent phrasing)
    p_alias = sub.add_parser("list-stages", help="Alias for describe-pipeline")
    p_alias.add_argument("--format", choices=["json", "table"], default="json")
    p_alias.add_argument("--core-only", action="store_true")
    p_alias.add_argument("--yaml", default=None)
    p_alias.add_argument("--project", default=None)
    p_alias.add_argument("--repo-root", default=".")
    p_alias.set_defaults(func=describe_pipeline)

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
