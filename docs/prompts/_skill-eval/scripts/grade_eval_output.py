#!/usr/bin/env python3
"""Grade eval outputs against expectations (keyword/heuristic checks)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPTS_DIR.parents[3]
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_SCRIPTS_DIR))

from skill_eval.grader import grade_output  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Grade eval output against expectations")
    parser.add_argument("output_file", type=Path, help="Response text/markdown file")
    parser.add_argument("expectations_file", type=Path, help="Expectations JSON")
    parser.add_argument("grading_file", type=Path, help="Output grading JSON path")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not print summary JSON to stdout",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print summary JSON to stdout (default when stdout is a TTY)",
    )
    args = parser.parse_args()

    text = args.output_file.read_text(encoding="utf-8")
    meta = json.loads(args.expectations_file.read_text(encoding="utf-8"))
    expectations = meta.get("expectations", [])
    negative = meta.get("negative", False)
    grading = grade_output(text, expectations, negative=negative)
    args.grading_file.write_text(json.dumps(grading, indent=2) + "\n", encoding="utf-8")

    print_summary = args.verbose or (not args.quiet and sys.stdout.isatty())
    if print_summary:
        print(json.dumps(grading["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
