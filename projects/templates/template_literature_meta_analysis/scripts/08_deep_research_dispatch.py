#!/usr/bin/env python3
"""Deep-research dispatch orchestrator (thin wrapper around the offline adapter).

Wires ``infrastructure.search.deep_research`` (a PAID, non-deterministic
capability) into the project. By default it REPLAYS a recorded report fixture:
deterministic, offline, CI-safe. The adapter also exposes the real
provider-neutral request a live ``submit`` would dispatch. Prints artifact paths
to stdout; never makes a network call or requires an API key.

Offline (default)::

    uv run python scripts/08_deep_research_dispatch.py
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _bootstrap import bootstrap_project

# include_infrastructure=True so ``infrastructure.search.deep_research`` resolves
# when the script is run standalone (outside the root pytest pythonpath).
PROJECT_ROOT = bootstrap_project(include_infrastructure=True)

from config import DATA_DIR as DEFAULT_DATA_DIR

from deep_research.deep_research_adapter import (
    build_offline_request,
    list_provider_profile,
    replay_recorded_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Demonstrate infrastructure.search.deep_research via offline fixture replay. "
            "No network, no API key required."
        )
    )
    parser.add_argument(
        "--query",
        default="Survey the cognitive-enhancement evidence for modafinil in healthy and sleep-deprived adults",
        help="Query used to build the (real) provider-neutral deep-research request.",
    )
    parser.add_argument(
        "--fixture",
        type=str,
        default=None,
        help="Optional explicit recorded-report JSON to replay (defaults to the bundled fixture).",
    )
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_DATA_DIR))
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("deep_research_dispatch")

    profile = list_provider_profile()
    request = build_offline_request(args.query)
    logger.info(
        "deep_research providers: catalogue=%s available=%s",
        profile["catalogue"],
        profile["available"],
    )

    if profile["available"]:
        logger.info("Live keys detected (%s); still replaying for determinism.", ", ".join(profile["available"]))

    fixture = Path(args.fixture) if args.fixture else None
    report = replay_recorded_report(fixture)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "deep_research_replay.json"
    payload = {
        "mode": "fixture-replay",
        "provider_profile": profile,
        "request": {"query": request.query, "provider": request.provider},
        "report": {
            "provider": report.provider,
            "job_id": report.job_id,
            "status": report.status,
            "query": report.query,
            "output_chars": len(report.output_text),
            "citation_count": report.citation_count,
            "citations": list(report.citations),
        },
    }
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("\nDeep research mode: fixture-replay (offline, deterministic)")
    print(f"Provider catalogue: {', '.join(profile['catalogue'])}")
    print(f"Replayed report: provider={report.provider} status={report.status} citations={report.citation_count}")
    print(str(output_path))


if __name__ == "__main__":
    main()
