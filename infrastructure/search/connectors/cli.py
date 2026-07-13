"""CLI for the connector registry — ``list-dbs`` and ``search`` subcommands.

Usage::

    python -m infrastructure.search.connectors list-dbs
    python -m infrastructure.search.connectors search openalex "CRISPR base editing"
    python -m infrastructure.search.connectors search --all "transformer attention"
"""

from __future__ import annotations

import argparse
import json
import sys

from infrastructure.search.connectors import get_registry, list_connectors
from infrastructure.search.connectors.types import ConnectorError, SearchOptions


def _cmd_list_dbs(args: argparse.Namespace) -> int:
    """List all registered connectors."""
    connectors = list_connectors()
    if args.json:
        output = [
            {
                "name": c.name,
                "domain": c.domain.value,
                "description": c.description,
            }
            for c in connectors
        ]
        print(json.dumps(output, indent=2))
    else:
        for c in connectors:
            print(f"  {c.name:<24} [{c.domain.value:<12}] {c.description}")
    return 0


def _cmd_search(args: argparse.Namespace) -> int:
    """Search one or all connectors."""
    opts = SearchOptions(max_results=args.max_results)
    connectors = get_registry().all() if args.all else []
    if not args.all:
        reg = get_registry()
        if not reg.has(args.connector):
            print(f"error: connector '{args.connector}' not found.", file=sys.stderr)
            return 1
        connectors = [reg.get(args.connector)]

    all_hits = []
    for connector in connectors:
        try:
            hits = connector.search(args.query, opts)
            all_hits.extend(hits)
        except ConnectorError as exc:
            print(f"warning: {connector.name}: {exc}", file=sys.stderr)

    if args.json:
        print(json.dumps([h.to_dict() for h in all_hits], indent=2))
    else:
        for h in all_hits:
            year = h.year or "?"
            print(f"  [{h.source}] {h.title!r} ({year})")
            if h.doi:
                print(f"    doi:{h.doi}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argparse parser."""
    parser = argparse.ArgumentParser(
        prog="connectors",
        description="Science-DB connector registry CLI",
    )
    sub = parser.add_subparsers(dest="command")

    # list-dbs
    p_list = sub.add_parser("list-dbs", help="List all registered connectors")
    p_list.add_argument("--json", action="store_true", help="Output as JSON")
    p_list.set_defaults(func=_cmd_list_dbs)

    # search
    p_search = sub.add_parser("search", help="Search a connector")
    p_search.add_argument("connector", nargs="?", default="", help="Connector name")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--all", action="store_true", help="Search all connectors")
    p_search.add_argument("--max-results", type=int, default=10)
    p_search.add_argument("--json", action="store_true", help="Output as JSON")
    p_search.set_defaults(func=_cmd_search)

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return int(args.func(args))


__all__ = ["build_parser", "main"]
