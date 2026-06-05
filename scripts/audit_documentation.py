#!/usr/bin/env python3
"""Emit the public documentation RedTeam audit report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import ensure_repo_root_on_path  # noqa: E402

ensure_repo_root_on_path()

from infrastructure.validation.docs.public_audit import (  # noqa: E402
    build_public_documentation_audit,
    format_audit_json,
    format_audit_markdown,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the documentation audit CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=Path("."),
        type=Path,
        help="Repository root. Defaults to the current directory.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Report format.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output file. Omit to print to stdout.",
    )
    args = parser.parse_args(argv)

    audit = build_public_documentation_audit(args.repo_root.resolve())
    text = format_audit_json(audit) if args.format == "json" else format_audit_markdown(audit)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised by direct CLI use
    raise SystemExit(main())
