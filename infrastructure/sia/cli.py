"""CLI for SIA task validation and run inspection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from infrastructure.core.logging.utils import get_logger

from .task_layout import validate_task_dir

logger = get_logger(__name__)


def _cmd_validate(task_dir: Path, *, as_json: bool) -> int:
    layout = validate_task_dir(task_dir)
    payload = {"task_dir": str(layout.task_dir), "status": "valid"}
    if as_json:
        print(json.dumps(payload))
    else:
        logger.info("Valid SIA task: %s", layout.task_dir)
        print(layout.task_dir)
    return 0


def _cmd_inspect_run(run_summary: Path, *, as_json: bool) -> int:
    if not run_summary.is_file():
        raise FileNotFoundError(f"run_summary.json not found: {run_summary}")
    payload = json.loads(run_summary.read_text(encoding="utf-8"))
    generations = payload.get("generations") or []
    summary = {
        "run_id": payload.get("run_id"),
        "live": payload.get("live"),
        "max_generations": payload.get("max_generations"),
        "generation_count": len(generations),
        "task_dir": payload.get("task_dir"),
    }
    if as_json:
        print(json.dumps(summary, indent=2))
    else:
        print(
            f"run_id={summary['run_id']} live={summary['live']} "
            f"generations={summary['generation_count']} task={summary['task_dir']}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    """Validate a SIA task directory or inspect a run summary."""
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    if raw_argv and raw_argv[0] not in {"validate", "inspect-run", "-h", "--help"} and not raw_argv[0].startswith("-"):
        raw_argv = ["validate", *raw_argv]

    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Shorthand: ``python -m infrastructure.sia.cli TASK_DIR`` runs ``validate TASK_DIR``. "
            "Omit TASK_DIR to validate the current working directory."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate_parser = sub.add_parser("validate", help="Validate task directory layout")
    validate_parser.add_argument(
        "task_dir",
        type=Path,
        nargs="?",
        default=Path("."),
        help="Task directory (default: current working directory)",
    )
    validate_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    inspect_parser = sub.add_parser("inspect-run", help="Summarize run_summary.json")
    inspect_parser.add_argument("run_summary", type=Path)
    inspect_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    args = parser.parse_args(raw_argv)
    try:
        if args.command == "inspect-run":
            return _cmd_inspect_run(args.run_summary, as_json=args.json)
        return _cmd_validate(args.task_dir, as_json=args.json)
    except (FileNotFoundError, OSError, ValueError) as exc:
        if args.json:
            print(json.dumps({"error": str(exc)}))
        else:
            print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
