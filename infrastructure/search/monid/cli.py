"""Command-line interface for the Monid client."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from typing import Any, Sequence

from infrastructure.core.cli_scaffold import emit_schema
from infrastructure.search.monid.client import MonidClient
from infrastructure.search.monid.errors import MonidError
from infrastructure.search.monid.pricing import format_pricing_table


def _serialize(obj: Any) -> Any:
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _serialize(v) for k, v in asdict(obj).items()}
    if isinstance(obj, tuple):
        return [_serialize(v) for v in obj]
    return obj


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argparse parser."""
    parser = argparse.ArgumentParser(prog="monid", description="Monid data-endpoint gateway")
    parser.add_argument("--base-url", default=None, help="override API host (testing)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_discover = sub.add_parser("discover", help="POST /v1/discover")
    p_discover.add_argument("query")
    p_discover.add_argument("--limit", type=int, default=5)
    p_discover.add_argument("--min-score", type=float, default=None)

    p_inspect = sub.add_parser("inspect", help="POST /v1/inspect")
    p_inspect.add_argument("provider")
    p_inspect.add_argument("endpoint")

    p_run = sub.add_parser("run", help="POST /v1/run")
    p_run.add_argument("provider")
    p_run.add_argument("endpoint")
    p_run.add_argument("--input", default="{}", help="JSON body for endpoint input")
    p_run.add_argument("--wait", action="store_true", help="poll until terminal status")

    p_get = sub.add_parser("get-run", help="GET /v1/runs/:runId")
    p_get.add_argument("run_id")

    sub.add_parser("balance", help="GET /v1/wallet/balance")
    sub.add_parser("pricing-table", help="print search API USD/1k comparison (offline)")

    p_schema = sub.add_parser("schema", help="Print this CLI's parameter schema as JSON and exit")
    p_schema.set_defaults(func=lambda _args: emit_schema(build_parser()))

    return parser


def run(args: argparse.Namespace) -> dict[str, Any]:
    """Execute the selected subcommand."""
    if args.command == "pricing-table":
        return {"markdown": format_pricing_table()}

    client = MonidClient.from_env(base_url=args.base_url)
    if args.command == "discover":
        return {"discover": _serialize(client.discover(args.query, limit=args.limit, min_score=args.min_score))}
    if args.command == "inspect":
        return {"inspect": _serialize(client.inspect(args.provider, args.endpoint))}
    if args.command == "run":
        try:
            payload = json.loads(args.input)
        except json.JSONDecodeError as exc:
            raise MonidError(f"invalid --input JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise MonidError("--input must be a JSON object")
        return {"run": _serialize(client.run(args.provider, args.endpoint, payload, wait=args.wait))}
    if args.command == "get-run":
        return {"run": _serialize(client.get_run(args.run_id))}
    if args.command == "balance":
        return {"balance": _serialize(client.balance())}
    raise MonidError(f"unknown command {args.command!r}")


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if hasattr(args, "func"):
        args.func(args)
        return 0
    try:
        payload = run(args)
    except MonidError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
