"""Declarative argparse construction for the orchestration CLI."""

from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    """Build the compatible top-level orchestration parser."""
    parser = argparse.ArgumentParser(
        prog="python -m infrastructure.orchestration",
        description="Research project pipeline orchestrator.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (defaults to the file's grandparent).",
    )
    sub = parser.add_subparsers(dest="command")

    pipe = sub.add_parser("pipeline", help="Run a single-project pipeline.")
    pipe.add_argument("--project", required=False, help="Project name.")
    pipe.add_argument("--all-projects", action="store_true")
    pipe.add_argument("--core-only", action="store_true")
    pipe.add_argument("--skip-infra", action="store_true")
    pipe.add_argument("--skip-llm", action="store_true")
    pipe.add_argument("--resume", action="store_true")
    pipe.add_argument(
        "--incremental",
        action="store_true",
        help="Enable incremental stage skipping when inputs/outputs are unchanged (opt-in; default off).",
    )

    multi = sub.add_parser("multi", help="Run all-projects orchestration.")
    multi.add_argument("--core-only", action="store_true")
    multi.add_argument("--skip-infra", action="store_true")
    multi.add_argument("--skip-llm", action="store_true")
    multi.add_argument(
        "--no-executive-report",
        action="store_true",
        help="Disable the cross-project executive report.",
    )

    secure = sub.add_parser(
        "secure",
        help="Run pipeline + steganography (or steganography-only).",
        description=(
            "Secure manuscript pipeline. Runs the standard pipeline for "
            "one project and then applies cryptographic PDF watermarking "
            "(steganography) to every emitted PDF. Use --steganography-only "
            "to skip the pipeline phase and post-process existing PDFs "
            "under projects/<name>/output/pdf/ (or output/<name>/pdf/)."
        ),
        epilog=(
            "Examples:\n"
            "  ./secure_run.sh --project my_project\n"
            "      Full pipeline + steganography for one project.\n"
            "\n"
            "  ./secure_run.sh --project my_project --core-only\n"
            "      Pipeline without LLM stages, then steganography.\n"
            "\n"
            "  ./secure_run.sh --steganography-only --project my_project\n"
            "      Skip the pipeline; only post-process one project's PDFs.\n"
            "\n"
            "  ./secure_run.sh --steganography-only\n"
            "      Skip the pipeline; post-process every discovered project.\n"
            "\n"
            "  ./secure_run.sh --deterministic --project my_project\n"
            "      Pin embedded build timestamp to `git log -1 --format=%cI`\n"
            "      so two consecutive runs produce byte-identical PDFs.\n"
            "\n"
            "  ./secure_run.sh --validate-kmyth --project my_project\n"
            "      Validate optional Kmyth/TPM tooling without running the pipeline."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    secure.add_argument(
        "--project",
        required=False,
        help=(
            "Project slug under projects/. Required for the pipeline phase; "
            "optional with --steganography-only (omit to sweep all projects)."
        ),
    )
    secure.add_argument(
        "--steganography-only",
        action="store_true",
        help=(
            "Skip the pipeline phase and only run steganography on existing "
            "PDFs. Use after a prior pipeline run to re-apply or refresh "
            "watermarks without re-rendering."
        ),
    )
    secure.add_argument("--skip-infra", action="store_true", help="Skip Layer-1 infrastructure tests.")
    secure.add_argument("--core-only", action="store_true", help="Run the 8-stage core pipeline (no LLM stages).")
    secure.add_argument("--resume", action="store_true", help="Resume the pipeline from the last checkpoint.")
    secure.add_argument(
        "--deterministic",
        action="store_true",
        help=(
            "Pin steganography build timestamp to the latest commit's author "
            "date (sets STEGANOGRAPHY_DETERMINISTIC=1) for byte-identical PDFs."
        ),
    )
    secure.add_argument(
        "--validate-kmyth",
        action="store_true",
        help="Validate optional Kmyth/TPM tooling and exit without rendering or sealing PDFs.",
    )

    menu = sub.add_parser("menu", help="Render the interactive menu.")
    menu.add_argument("--project", default=None)
    sub.add_parser("list-projects", help="List discovered projects, one per line.")

    link = sub.add_parser("link-projects", help="Symlink private lifecycle projects into local mirrors.")
    link.add_argument("--dry-run", action="store_true", help="Report without changing anything.")
    link.add_argument("--no-prune", action="store_true", help="Keep stale managed links.")

    promotion = sub.add_parser(
        "promotion-check",
        help="Validate a private-project promotion attestation without moving or publishing anything.",
    )
    promotion.add_argument("--attestation", type=Path, required=True, help="Offline promotion attestation YAML.")
    sub.add_parser("schema", help="Print this CLI's parameter schema as JSON and exit.")
    return parser


__all__ = ["build_parser"]
