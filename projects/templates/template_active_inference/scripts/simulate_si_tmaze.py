#!/usr/bin/env python3
"""Run pymdp sophisticated-inference T-maze simulation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from simulation.pymdp_config import apply_pymdp_overrides, load_pymdp_config
from simulation.si_artifacts import write_policy_comparison, write_policy_posterior_grid
from simulation.si_runner import pymdp_available, run_and_persist


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description="Run pymdp T-maze state or policy inference and write SI artifacts.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to pymdp.yaml (default: project-root pymdp.yaml)",
    )
    parser.add_argument("--steps", type=int, default=None, help="Rollout length (overrides config)")
    parser.add_argument(
        "--horizon",
        type=int,
        default=None,
        help="Agent policy_len / planning horizon (overrides config)",
    )
    parser.add_argument("--seed", type=int, default=None, help="Random seed (overrides config)")
    parser.add_argument(
        "--mode",
        choices=("state_inference", "policy_inference"),
        default=None,
        help="Simulation mode (default: config file)",
    )
    parser.add_argument(
        "--log-disabled",
        action="store_true",
        help="Disable JSONL logging even when enabled in config",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if not pymdp_available():
        print(
            "pymdp not installed; simulate_si_tmaze.py requires inferactively-pymdp "
            "(see pyproject.toml). Install deps with `uv sync` in the project root.",
            file=sys.stderr,
        )
        return 1

    config = load_pymdp_config(PROJECT_ROOT, config_path=args.config)
    config = apply_pymdp_overrides(
        config,
        steps=args.steps,
        horizon=args.horizon,
        seed=args.seed,
        mode=args.mode,
        logging_enabled=False if args.log_disabled else None,
    )
    result = run_and_persist(PROJECT_ROOT, config=config)
    for name, path in result["paths"].items():
        print(f"{name}: {path}")
    print(f"policy_comparison: {write_policy_comparison(PROJECT_ROOT)}")
    print(f"policy_posterior_grid: {write_policy_posterior_grid(PROJECT_ROOT)}")
    log_path = PROJECT_ROOT / config.logging.path
    if config.logging.enabled:
        print(f"log: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
