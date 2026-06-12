#!/usr/bin/env python3
"""Thin orchestrator for the deterministic SIA harness loop."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[2]
for path in (PROJECT_ROOT, PROJECT_ROOT / "src", REPO_ROOT):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from infrastructure.core.logging.utils import get_logger

from sia_loop_impl import run_sia_loop_project

logger = get_logger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        default=str(PROJECT_ROOT),
        help="Project root directory",
    )
    parser.add_argument(
        "--live-sia",
        action="store_true",
        help="Run live target subprocess (optional LLM feedback when Ollama is available).",
    )
    args = parser.parse_args(argv)
    project_root = Path(args.project_root).resolve()
    logger.info("Running SIA loop (live=%s)", args.live_sia)
    result = run_sia_loop_project(project_root, live=args.live_sia)
    summary = json.loads(result.run_summary.read_text(encoding="utf-8"))
    print(result.report_path)
    print(result.run_summary)
    print(json.dumps({"generations": len(summary.get("generations", []))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
