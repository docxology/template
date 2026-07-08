#!/usr/bin/env python3
"""Write manuscript_variables.json and resolve {{token}} placeholders for PDF."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from manuscript.hydrate import write_resolved_manuscript
from manuscript.sheaf import compose_all_sections
from manuscript.variables import generate_variables
from roadmap_tracks import run_semantic_fixed_point, write_manuscript_staleness_report


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-draft",
        action="store_true",
        help="Allow missing analysis outputs (non-pipeline draft mode)",
    )
    args = parser.parse_args(argv)

    out = PROJECT_ROOT / "output" / "data" / "manuscript_variables.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    variables = generate_variables(
        PROJECT_ROOT,
        require_analysis_outputs=not args.allow_draft,
    )
    out.write_text(json.dumps(variables, indent=2), encoding="utf-8")
    if args.allow_draft:
        # Draft hydration should stay below the repo's per-test timeout and
        # tolerate missing analysis artifacts. The strict pipeline path below
        # still refreshes the full sheaf-track and semantic artifact surface.
        compose_all_sections(PROJECT_ROOT)
        variables = generate_variables(PROJECT_ROOT, require_analysis_outputs=False)
        out.write_text(json.dumps(variables, indent=2), encoding="utf-8")
        resolved_dir = write_resolved_manuscript(PROJECT_ROOT, variables)
        staleness_path = write_manuscript_staleness_report(PROJECT_ROOT)
        print(out)
        print(resolved_dir)
        print(staleness_path)
        return 0

    semantic_paths = run_semantic_fixed_point(
        PROJECT_ROOT,
        require_analysis_outputs=not args.allow_draft,
    )
    resolved_dir = PROJECT_ROOT / "output" / "manuscript"
    staleness_path = PROJECT_ROOT / "output" / "reports" / "manuscript_staleness_report.json"
    print(out)
    for path in semantic_paths.values():
        print(path)
    print(resolved_dir)
    print(staleness_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
