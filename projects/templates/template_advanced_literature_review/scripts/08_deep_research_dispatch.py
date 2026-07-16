#!/usr/bin/env python3
"""Run the advanced exemplar's deterministic deep-research replay stage.

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
from deep_research.dispatch import dispatch_offline_replay


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Demonstrate infrastructure.search.deep_research via offline fixture replay. "
            "No network, no API key required."
        )
    )
    parser.add_argument(
        "--query",
        default="Survey robust evidence and uncertainty in exoplanet atmosphere characterization",
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

    fixture = Path(args.fixture) if args.fixture else None
    replay = dispatch_offline_replay(
        args.query,
        Path(args.output_dir),
        fixture_path=fixture,
    )
    profile = replay.provider_profile
    logger.info(
        "deep_research providers: catalogue=%s available=%s",
        profile["catalogue"],
        profile["available"],
    )

    if profile["available"]:
        logger.info(
            "Live keys detected (%s); still replaying for determinism.",
            ", ".join(profile["available"]),
        )

    print("\nDeep research mode: fixture-replay (offline, deterministic)")
    print(f"Provider catalogue: {', '.join(profile['catalogue'])}")
    print(
        f"Replayed report: provider={replay.result.provider} "
        f"status={replay.result.status} citations={len(replay.result.citations)}"
    )
    print(str(replay.output_path))


if __name__ == "__main__":
    main()
