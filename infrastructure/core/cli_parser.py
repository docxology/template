"""CLI argument parser for core infrastructure commands.

Defines the argument parser and subcommands for pipeline, multi-project,
inventory, and discovery operations.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser for core CLI commands."""
    parser = argparse.ArgumentParser(
        description="Core infrastructure CLI for pipeline operations",
        prog="python -m infrastructure.core.cli",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Pipeline execution command
    pipeline_parser = subparsers.add_parser("pipeline", help="Execute pipeline for a project")
    pipeline_parser.add_argument(
        "pipeline_type", choices=["full", "core"], help="Type of pipeline to execute"
    )
    pipeline_parser.add_argument(
        "--project", required=True, help="Project name to execute pipeline for"
    )
    pipeline_parser.add_argument(
        "--repo-root", type=Path, default=Path.cwd(), help="Repository root directory"
    )
    pipeline_parser.add_argument(
        "--skip-infra",
        action="store_true",
        help="Skip infrastructure tests (already run)",
    )
    pipeline_parser.add_argument(
        "--resume", action="store_true", help="Resume pipeline from checkpoint"
    )

    # Multi-project execution command
    multi_parser = subparsers.add_parser(
        "multi-project", help="Execute pipeline across multiple projects"
    )
    multi_parser.add_argument(
        "execution_type",
        choices=["full", "core", "full-no-infra", "core-no-infra"],
        help="Type of multi-project execution",
    )
    multi_parser.add_argument(
        "--repo-root", type=Path, default=Path.cwd(), help="Repository root directory"
    )
    multi_parser.add_argument(
        "--projects", nargs="+", help="Specific projects to execute (default: all)"
    )

    # File inventory command
    inventory_parser = subparsers.add_parser("inventory", help="Generate file inventory report")
    inventory_parser.add_argument("output_dir", type=Path, help="Output directory to scan")
    inventory_parser.add_argument(
        "--format",
        choices=["text", "json", "html"],
        default="text",
        help="Output format",
    )
    inventory_parser.add_argument(
        "--categories", nargs="+", help="Categories to scan (default: all)"
    )

    # Project discovery command
    discover_parser = subparsers.add_parser("discover", help="Discover available projects")
    discover_parser.add_argument(
        "--repo-root", type=Path, default=Path.cwd(), help="Repository root directory"
    )
    discover_parser.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format"
    )

    return parser
