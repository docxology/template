#!/usr/bin/env python3
"""CodeGraph local-integration helper — thin wrapper."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.project.codegraph import (  # noqa: E402
    build_codegraph_files_command,
    build_codegraph_init_command,
    is_codegraph_available,
    verify_codegraph_scope_payload,
)


def _print_command(command_name: str, argv: tuple[str, ...]) -> None:
    print(f"{command_name}: {' '.join(argv)}")


def _commands(path: Path) -> int:
    init_command = build_codegraph_init_command(path)
    files_command = build_codegraph_files_command(path)
    print(f"codegraph on PATH: {is_codegraph_available()}")
    _print_command("init", init_command.argv)
    _print_command("scope-json", files_command.argv)
    print("verify-scope: codegraph files <path> --json | uv run python scripts/codegraph_local.py verify-scope")
    return 0


def _verify_scope(payload: str) -> int:
    unexpected = verify_codegraph_scope_payload(payload)
    if not unexpected:
        print("CodeGraph scope check: no private/local project paths found.")
        return 0
    print("CodeGraph scope check failed; unexpected private/local project paths were indexed:")
    for path in unexpected:
        print(f"  {path}")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    commands_parser = subparsers.add_parser("commands", help="Print recommended CodeGraph commands.")
    commands_parser.add_argument("path", nargs="?", type=Path, default=REPO_ROOT)

    subparsers.add_parser("verify-scope", help="Read CodeGraph files JSON from stdin and verify scope.")

    args = parser.parse_args(argv)
    if args.command == "commands":
        return _commands(args.path)
    if args.command == "verify-scope":
        return _verify_scope(sys.stdin.read())
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
