"""Shared CLI scaffold: uniform flags + argparse schema introspection.

73 ``cli.py`` modules hand-roll their own ``argparse`` setup, so flag names and
conventions drift and an agent cannot assume a uniform invocation/JSON contract.
This module is the additive, opt-in convergence point. It does NOT rewrite any
existing CLI — modules adopt it incrementally:

* ``add_repo_root_arg`` / ``add_project_arg`` / ``add_format_arg`` /
  ``add_verbose_arg`` / ``add_schema_flag`` — shared flag definitions so every
  adopting CLI names them identically.
* :func:`parser_schema` — introspect an :class:`argparse.ArgumentParser` (and its
  subparsers) into a machine-readable schema, so an agent can fetch a command's
  parameter contract without scraping ``--help`` text.
* :func:`emit_schema` — print that schema as JSON to stdout (exit code 0).

The schema is the per-command counterpart to the package-wide operation catalog
in :mod:`infrastructure.skills.operation_registry`, and feeds an MCP tool's
``inputSchema`` directly.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

__all__ = [
    "add_format_arg",
    "add_project_arg",
    "add_repo_root_arg",
    "add_schema_flag",
    "add_verbose_arg",
    "emit_schema",
    "parser_schema",
]


def add_repo_root_arg(parser: argparse.ArgumentParser, *, default: str = ".") -> None:
    """Add the shared ``--repo-root`` flag."""
    parser.add_argument("--repo-root", default=default, help="Repository root (default: current directory)")


def add_project_arg(parser: argparse.ArgumentParser, *, required: bool = False) -> None:
    """Add the shared ``--project`` flag (semantics documented per the project arg contract)."""
    parser.add_argument("--project", required=required, default=None, help="Target project name")


def add_format_arg(
    parser: argparse.ArgumentParser,
    *,
    choices: tuple[str, ...] = ("json", "table"),
    default: str = "json",
) -> None:
    """Add the shared ``--format`` flag (machine-readable default)."""
    parser.add_argument("--format", choices=list(choices), default=default, help=f"Output format (default: {default})")


def add_verbose_arg(parser: argparse.ArgumentParser) -> None:
    """Add the shared ``-v/--verbose`` flag."""
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")


def add_schema_flag(parser: argparse.ArgumentParser) -> None:
    """Add the shared ``--schema`` flag (emit JSON parameter schema and exit)."""
    parser.add_argument(
        "--schema",
        action="store_true",
        help="Print this command's parameter schema as JSON and exit",
    )


def _type_name(action: argparse.Action) -> str:
    """Best-effort human/JSON name for an action's type."""
    if action.type is None:
        if isinstance(action, (argparse._StoreTrueAction, argparse._StoreFalseAction)):
            return "boolean"
        return "string"
    name = getattr(action.type, "__name__", None)
    mapping = {"str": "string", "int": "integer", "float": "number", "bool": "boolean", "Path": "path"}
    return mapping.get(name or "", name or "string")


def _action_schema(action: argparse.Action) -> dict[str, Any] | None:
    """Schema for one argparse action, or None for help/internal actions."""
    if isinstance(action, argparse._HelpAction):
        return None
    if isinstance(action, argparse._SubParsersAction):
        return None
    positional = not action.option_strings
    entry: dict[str, Any] = {
        "name": action.dest,
        "flags": list(action.option_strings),
        "positional": positional,
        "required": bool(action.required) or (positional and action.nargs not in ("?", "*")),
        "type": _type_name(action),
        "help": action.help,
    }
    if action.choices is not None:
        entry["choices"] = list(action.choices)
    if action.default is not None and action.default is not argparse.SUPPRESS:
        default = action.default
        entry["default"] = default if isinstance(default, (str, int, float, bool)) else str(default)
    return entry


def parser_schema(parser: argparse.ArgumentParser) -> dict[str, Any]:
    """Introspect a parser (and its subparsers) into a machine-readable schema."""
    options: list[dict[str, Any]] = []
    subcommands: dict[str, Any] = {}
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for name, subparser in action.choices.items():
                subcommands[name] = parser_schema(subparser)
            continue
        entry = _action_schema(action)
        if entry is not None:
            options.append(entry)
    schema: dict[str, Any] = {"prog": parser.prog, "description": parser.description, "options": options}
    if subcommands:
        schema["subcommands"] = subcommands
    return schema


def emit_schema(parser: argparse.ArgumentParser) -> int:
    """Print ``parser_schema(parser)`` as JSON to stdout and return 0."""
    sys.stdout.write(json.dumps(parser_schema(parser), indent=2, ensure_ascii=False) + "\n")
    return 0
