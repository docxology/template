"""CLI for skill discovery and manifest generation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

from .discovery import (
    discover_skills,
    manifest_matches_discovery,
    skill_descriptors_as_json_serializable,
    write_skill_manifest,
)

logger = get_logger(__name__)


def _repo_root_from_args(args: argparse.Namespace) -> Path:
    return Path(args.repo_root).resolve()


def cmd_list_json(args: argparse.Namespace) -> int:
    root = _repo_root_from_args(args)
    skills = discover_skills(root, search_roots=args.roots)
    payload = skill_descriptors_as_json_serializable(skills)
    sys.stdout.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return 0


def cmd_write(args: argparse.Namespace) -> int:
    root = _repo_root_from_args(args)
    out = Path(args.output) if args.output else None
    path = write_skill_manifest(root, output_path=out, search_roots=args.roots)
    logger.info("Wrote skill manifest: %s", path)
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    root = _repo_root_from_args(args)
    mpath = Path(args.manifest)
    if not mpath.is_absolute():
        mpath = (root / mpath).resolve()
    else:
        mpath = mpath.resolve()
    ok, msg = manifest_matches_discovery(root, mpath, search_roots=args.roots)
    if ok:
        logger.info("%s", msg)
        return 0
    logger.error("%s", msg)
    return 1


def _add_shared_cli_args(p: argparse.ArgumentParser) -> None:
    """Options shared by all subcommands (must live on subparsers so flags can follow the verb)."""
    p.add_argument(
        "--repo-root",
        default=".",
        help="Repository root (default: current directory)",
    )
    p.add_argument(
        "--roots",
        nargs="*",
        default=None,
        metavar="DIR",
        help=(
            "Override search roots relative to repo root "
            "(default: infrastructure + projects/cognitive_case_diagrams/src). "
            "Example: write --roots infrastructure docs"
        ),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Discover SKILL.md files and maintain .cursor/skill_manifest.json",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list-json", help="Print skills as JSON to stdout")
    _add_shared_cli_args(p_list)
    p_list.set_defaults(func=cmd_list_json)

    p_write = sub.add_parser("write", help="Write skill manifest JSON")
    _add_shared_cli_args(p_write)
    p_write.add_argument(
        "--output",
        default=None,
        help="Output file (default: .cursor/skill_manifest.json under repo root)",
    )
    p_write.set_defaults(func=cmd_write)

    p_check = sub.add_parser("check", help="Verify manifest matches discovery")
    _add_shared_cli_args(p_check)
    p_check.add_argument(
        "--manifest",
        default=".cursor/skill_manifest.json",
        help="Manifest path relative to repo root unless absolute",
    )
    p_check.set_defaults(func=cmd_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.roots is not None and len(args.roots) == 0:
        parser.error("--roots, if passed, must list at least one directory")
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
