"""Command-line interface for the Exa search interfaces.

Thin orchestrator: parses args, constructs :class:`ExaClient` from the
environment, delegates to an interface, and prints JSON. All logic lives in the
interface/model modules.

Examples::

    python -m infrastructure.search.exa search "vector database benchmarks" --num-results 5
    python -m infrastructure.search.exa contents https://example.com/post --text
    python -m infrastructure.search.exa answer "what is retrieval-augmented generation?"
    python -m infrastructure.search.exa find-similar https://arxiv.org/abs/1706.03762
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from typing import Any, Sequence

from infrastructure.core.cli_scaffold import emit_schema
from infrastructure.search.exa.client import ExaClient
from infrastructure.search.exa.config import VALID_SEARCH_TYPES
from infrastructure.search.exa.errors import ExaError


def _domains(value: str | None) -> list[str] | None:
    return [d.strip() for d in value.split(",") if d.strip()] if value else None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="exa", description="Exa search interfaces")
    parser.add_argument("--base-url", default=None, help="override API host (testing)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="POST /search")
    p_search.add_argument("query")
    p_search.add_argument("--type", choices=sorted(VALID_SEARCH_TYPES), default=None)
    p_search.add_argument("--num-results", type=int, default=None)
    p_search.add_argument("--category", default=None)
    p_search.add_argument("--include-domains", default=None, help="comma-separated")
    p_search.add_argument("--exclude-domains", default=None, help="comma-separated")
    p_search.add_argument("--text", action="store_true", help="request full text")
    p_search.add_argument("--no-highlights", action="store_true", help="disable default highlights")

    p_contents = sub.add_parser("contents", help="POST /contents")
    p_contents.add_argument("urls", nargs="+")
    p_contents.add_argument("--text", action="store_true")

    p_answer = sub.add_parser("answer", help="POST /answer")
    p_answer.add_argument("query")
    p_answer.add_argument("--text", action="store_true")

    p_similar = sub.add_parser("find-similar", help="POST /findSimilar")
    p_similar.add_argument("url")
    p_similar.add_argument("--num-results", type=int, default=None)

    p_schema = sub.add_parser("schema", help="Print this CLI's parameter schema as JSON and exit")
    p_schema.set_defaults(func=lambda _args: emit_schema(build_parser()))

    return parser


def run(args: argparse.Namespace) -> dict[str, Any]:
    client = ExaClient.from_env(base_url=args.base_url)
    if args.command == "search":
        resp = client.search(
            args.query,
            type=args.type,
            num_results=args.num_results,
            category=args.category,
            include_domains=_domains(args.include_domains),
            exclude_domains=_domains(args.exclude_domains),
            text=True if args.text else None,
            highlights=None if (args.text or args.no_highlights) else True,
        )
        return {"results": [asdict(r) for r in resp.results], "requestId": resp.request_id}
    if args.command == "contents":
        resp = client.contents(args.urls, text=True if args.text else None)
        return {"results": [asdict(r) for r in resp.results], "requestId": resp.request_id}
    if args.command == "answer":
        resp = client.answer(args.query, text=True if args.text else None)
        return {"answer": resp.answer, "citations": [asdict(c) for c in resp.citations]}
    if args.command == "find-similar":
        resp = client.find_similar(args.url, num_results=args.num_results)
        return {"results": [asdict(r) for r in resp.results], "requestId": resp.request_id}
    raise ExaError(f"unknown command {args.command!r}")  # pragma: no cover - argparse guards


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    func = getattr(args, "func", None)
    if func is not None:
        result = func(args)
        return int(result)
    try:
        print(json.dumps(run(args), indent=2, ensure_ascii=False))
    except ExaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
