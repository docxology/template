"""Command-line interface for deep research dispatch.

Thin orchestrator mirroring the ``literature`` and ``exa`` CLIs: parses args,
constructs :class:`DeepResearchClient` from the environment, delegates to the
client/provider modules, and prints JSON. All logic lives in the library.

Requires the ``deep-research`` dependency group (``uv sync --group
deep-research``) and provider keys in the environment (``OPENAI_API_KEY``
and/or ``GEMINI_API_KEY``).

Examples::

    python -m infrastructure.search.deep_research providers
    python -m infrastructure.search.deep_research submit "survey of X" --provider openai
    python -m infrastructure.search.deep_research poll openai resp_abc123
    python -m infrastructure.search.deep_research run-project projects/templates/template_active_inference \
        "Review this manuscript; suggest fixes and new citations." --providers openai
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from typing import Any, Sequence

from infrastructure.search.deep_research.client import DeepResearchClient
from infrastructure.search.deep_research.models import DeepResearchJobHandle, DeepResearchRequest, DeepResearchResult


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deep_research", description="Deep research provider dispatch")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("providers", help="list providers usable with current environment")

    p_submit = sub.add_parser("submit", help="submit a query and print the job handle")
    p_submit.add_argument("query")
    p_submit.add_argument("--provider", choices=("auto", "openai", "gemini"), default="auto")

    p_poll = sub.add_parser("poll", help="poll a submitted job once and print its state")
    p_poll.add_argument("provider", choices=("openai", "gemini"))
    p_poll.add_argument("job_id")

    p_run = sub.add_parser("run-project", help="package a project tree, run providers to completion, save reports")
    p_run.add_argument("project_root")
    p_run.add_argument("query")
    p_run.add_argument("--providers", default="openai,gemini", help="comma-separated provider list")
    p_run.add_argument("--poll-interval", type=float, default=15.0)

    return parser


def _handle_dict(handle: DeepResearchJobHandle) -> dict[str, Any]:
    return {"provider": handle.provider, "job_id": handle.job_id, "status": handle.status}


def _result_dict(result: DeepResearchResult) -> dict[str, Any]:
    return {
        "provider": result.provider,
        "job_id": result.job_id,
        "status": result.status,
        "output_chars": len(result.output_text),
        "citations": [{"title": c.title, "url": c.url} for c in result.citations],
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    client = DeepResearchClient.from_env()
    if args.command == "providers":
        return {
            "available": list(client.available_providers()),
            "openai_model": client.config.openai_model,
            "gemini_agent": client.config.gemini_agent,
        }
    if args.command == "submit":
        handle = client.submit(replace(DeepResearchRequest(query=args.query), provider=args.provider))
        return _handle_dict(handle)
    if args.command == "poll":
        request = DeepResearchRequest(query="", provider=args.provider)
        handle = DeepResearchJobHandle(provider=args.provider, job_id=args.job_id, status="unknown", request=request)
        return _result_dict(client.poll(handle))
    if args.command == "run-project":
        providers = tuple(p.strip() for p in args.providers.split(",") if p.strip())
        bundles = client.submit_project_and_save_reports(
            args.project_root,
            args.query,
            providers=providers,
            poll_interval_seconds=args.poll_interval,
        )
        return {
            provider: {"markdown": str(bundle.markdown_path), "json": str(bundle.json_path)}
            for provider, bundle in bundles.items()
        }
    raise ValueError(f"unknown command {args.command!r}")  # pragma: no cover - argparse guards


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        print(json.dumps(run(args), indent=2, ensure_ascii=False))
    except Exception as exc:  # noqa: BLE001 - CLI boundary: report and exit nonzero
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
