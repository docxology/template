"""Application logic for the opt-in Connector Search pipeline stage.

The numbered script in ``scripts/pipeline`` is intentionally only a bootstrap
shim.  Configuration parsing, project resolution, connector dispatch, failure
isolation, and result serialisation live here so they can be exercised without
executing an external network service.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import yaml

from infrastructure.core.logging.utils import get_logger, log_header, log_success
from infrastructure.core.project_paths import find_repo_root, resolve_project_root
from infrastructure.search.connectors import ConnectorRegistry, get_registry
from infrastructure.search.connectors.types import SearchOptions

logger = get_logger(__name__)

SUCCESS = 0
FAILURE = 1
SKIP = 2
DEFAULT_MAX_RESULTS = 10
DEFAULT_OUTPUT = Path("output/data/connector_search/results.json")
_CONFIG_KEYS = frozenset({"enabled", "max_results", "connectors"})


class ConnectorSearchConfigurationError(ValueError):
    """Raised when the Stage 08 project configuration is malformed."""


class ConnectorSearchNotConfigured(RuntimeError):
    """Raised when Stage 08 should perform its documented graceful skip."""


@dataclass(frozen=True)
class ConnectorSearchRequest:
    """One connector/query pair from the stage configuration."""

    connector: str
    query: str


@dataclass(frozen=True)
class ConnectorSearchPlan:
    """Validated inputs for one Stage 08 execution."""

    project: str
    project_dir: Path
    output_path: Path
    max_results: int
    requests: tuple[ConnectorSearchRequest, ...]


def _positive_int(value: str) -> int:
    """Parse an argparse value that must be strictly positive."""
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    """Build the Stage 08 command-line parser."""
    parser = argparse.ArgumentParser(description="Connector Search Stage")
    parser.add_argument("--project", default="project", help="Project name in projects/")
    parser.add_argument(
        "--connector",
        help="Run one connector directly; requires --query and bypasses project config",
    )
    parser.add_argument(
        "--query",
        help="Run one query directly; requires --connector and bypasses project config",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=("Output JSON path (default: <project>/output/data/connector_search/results.json)"),
    )
    parser.add_argument(
        "--max-results",
        type=_positive_int,
        help=f"Maximum results per query (default: config value or {DEFAULT_MAX_RESULTS})",
    )
    return parser


def _load_yaml_mapping(config_path: Path) -> dict[str, Any]:
    """Read a YAML file and require a mapping at its root."""
    try:
        raw_payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConnectorSearchConfigurationError(f"failed to load {config_path}: {exc}") from exc
    payload = {} if raw_payload is None else raw_payload
    if not isinstance(payload, dict):
        raise ConnectorSearchConfigurationError(f"{config_path} must contain a YAML mapping")
    return payload


def _configured_requests(config_path: Path) -> tuple[tuple[ConnectorSearchRequest, ...], int]:
    """Load connector/query pairs and the result cap from manuscript config."""
    if not config_path.is_file():
        raise ConnectorSearchNotConfigured(f"no connector_search config found at {config_path}")

    payload = _load_yaml_mapping(config_path)
    raw_block = payload.get("connector_search")
    if raw_block is None:
        raise ConnectorSearchNotConfigured(f"no connector_search block found in {config_path}")
    if not isinstance(raw_block, dict):
        raise ConnectorSearchConfigurationError("connector_search must be a YAML mapping")
    unknown_keys = set(raw_block) - _CONFIG_KEYS
    if unknown_keys:
        rendered = ", ".join(sorted(str(key) for key in unknown_keys))
        raise ConnectorSearchConfigurationError(f"unknown connector_search key(s): {rendered}")

    enabled = raw_block.get("enabled", False)
    if not isinstance(enabled, bool):
        raise ConnectorSearchConfigurationError("connector_search.enabled must be true or false")
    if not enabled:
        raise ConnectorSearchNotConfigured("connector_search is disabled")

    max_results = raw_block.get("max_results", DEFAULT_MAX_RESULTS)
    if not isinstance(max_results, int) or isinstance(max_results, bool) or max_results <= 0:
        raise ConnectorSearchConfigurationError("connector_search.max_results must be a positive integer")

    raw_connectors = raw_block.get("connectors", {})
    if not isinstance(raw_connectors, dict):
        raise ConnectorSearchConfigurationError("connector_search.connectors must map connector IDs to query lists")

    requests: list[ConnectorSearchRequest] = []
    for raw_connector, raw_queries in raw_connectors.items():
        if not isinstance(raw_connector, str) or not raw_connector.strip():
            raise ConnectorSearchConfigurationError("connector_search connector IDs must not be empty")
        connector = raw_connector.strip()
        if not isinstance(raw_queries, list):
            raise ConnectorSearchConfigurationError(
                f"connector_search.connectors.{connector} must be a list of queries"
            )
        for raw_query in raw_queries:
            if not isinstance(raw_query, str) or not raw_query.strip():
                raise ConnectorSearchConfigurationError(
                    f"connector_search.connectors.{connector} contains an empty or non-string query"
                )
            requests.append(ConnectorSearchRequest(connector=connector, query=raw_query.strip()))

    if not requests:
        raise ConnectorSearchNotConfigured("no connector searches are configured")
    return tuple(requests), max_results


def build_plan(
    *,
    repo_root: Path,
    project: str,
    connector: str | None = None,
    query: str | None = None,
    max_results: int | None = None,
    output: Path | None = None,
) -> ConnectorSearchPlan:
    """Resolve and validate all inputs needed by Stage 08."""
    requests: tuple[ConnectorSearchRequest, ...]
    project_dir = resolve_project_root(repo_root, project)
    if not project_dir.is_dir():
        raise ConnectorSearchNotConfigured(f"project directory not found: {project_dir}")

    if bool(connector) != bool(query):
        raise ConnectorSearchConfigurationError("--connector and --query must be supplied together")

    if connector and query:
        connector = connector.strip()
        query = query.strip()
        if not connector or not query:
            raise ConnectorSearchConfigurationError("--connector and --query must contain non-whitespace text")
        requests = (
            ConnectorSearchRequest(
                connector=connector,
                query=query,
            ),
        )
        configured_max_results = DEFAULT_MAX_RESULTS
    else:
        requests, configured_max_results = _configured_requests(project_dir / "manuscript" / "config.yaml")

    selected_max_results = configured_max_results if max_results is None else max_results
    if not isinstance(selected_max_results, int) or isinstance(selected_max_results, bool) or selected_max_results <= 0:
        raise ConnectorSearchConfigurationError("max_results must be a positive integer")
    output_path = output or project_dir / DEFAULT_OUTPUT
    if not output_path.is_absolute():
        output_path = repo_root / output_path

    return ConnectorSearchPlan(
        project=project,
        project_dir=project_dir,
        output_path=output_path,
        max_results=selected_max_results,
        requests=requests,
    )


def execute_plan(
    plan: ConnectorSearchPlan,
    *,
    registry: ConnectorRegistry | None = None,
) -> tuple[dict[str, Any], bool]:
    """Execute a plan, isolating connector failures and returning its report."""
    active_registry = registry or get_registry()
    searches: list[dict[str, Any]] = []
    successful = 0
    total_hits = 0

    for request in plan.requests:
        logger.info(f"Searching {request.connector}: {request.query}")
        try:
            connector = active_registry.get(request.connector)
            hits = connector.search(
                request.query,
                SearchOptions(max_results=plan.max_results),
            )
        except Exception as exc:  # noqa: BLE001 - connector boundary records per-source failures
            logger.error(f"  → Failed: {exc}")
            searches.append(
                {
                    "connector": request.connector,
                    "query": request.query,
                    "status": "error",
                    "error": str(exc),
                    "results": [],
                }
            )
            continue

        serialised_hits = [hit.to_dict() for hit in hits]
        searches.append(
            {
                "connector": request.connector,
                "query": request.query,
                "status": "success",
                "error": None,
                "results": serialised_hits,
            }
        )
        successful += 1
        total_hits += len(hits)
        logger.info(f"  → {len(hits)} results")

    failed = len(searches) - successful
    report: dict[str, Any] = {
        "schema_version": 1,
        "project": plan.project,
        "max_results": plan.max_results,
        "summary": {
            "searches": len(searches),
            "successful": successful,
            "failed": failed,
            "hits": total_hits,
        },
        "searches": searches,
    }
    return report, failed == 0


def write_report(report: dict[str, Any], output_path: Path) -> None:
    """Write a deterministic, human-readable Stage 08 report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    repo_root: Path | None = None,
    registry: ConnectorRegistry | None = None,
) -> int:
    """Run Stage 08 and return its documented process exit code."""
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    root = (repo_root or find_repo_root()).resolve()

    log_header(f"STAGE 08: Connector Search (Project: {args.project})", logger)
    try:
        plan = build_plan(
            repo_root=root,
            project=args.project,
            connector=args.connector,
            query=args.query,
            max_results=args.max_results,
            output=args.output,
        )
    except ConnectorSearchNotConfigured as exc:
        logger.info(f"{exc} — skipping")
        return SKIP
    except ConnectorSearchConfigurationError as exc:
        logger.error(f"Invalid connector search configuration: {exc}")
        return FAILURE

    report, success = execute_plan(plan, registry=registry)
    try:
        write_report(report, plan.output_path)
    except OSError as exc:
        logger.error(f"Failed to write connector search results: {exc}")
        return FAILURE

    logger.info(f"Results written to {plan.output_path}")
    if success:
        log_success("Connector search complete", logger)
        return SUCCESS
    return FAILURE


__all__ = [
    "ConnectorSearchConfigurationError",
    "ConnectorSearchNotConfigured",
    "ConnectorSearchPlan",
    "ConnectorSearchRequest",
    "build_parser",
    "build_plan",
    "execute_plan",
    "main",
    "write_report",
]
