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
from manuscript.sheaf.semantic import write_semantic_gluing_outputs
from manuscript.variables import generate_variables
from roadmap_tracks import (
    write_integration_audit_artifacts,
    write_manuscript_staleness_report,
    write_sheaf_track_artifacts,
)


def main(argv: list[str] | None = None) -> int:
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
    write_integration_audit_artifacts(PROJECT_ROOT)
    write_sheaf_track_artifacts(PROJECT_ROOT)
    semantic_paths = write_semantic_gluing_outputs(PROJECT_ROOT)

    # Recompose after canonical semantic outputs exist so generated layer tables
    # reflect final artifact producers, claims, restrictions, and track scope.
    compose_all_sections(PROJECT_ROOT)
    resolved_dir = PROJECT_ROOT / "output" / "manuscript"
    staleness_path = PROJECT_ROOT / "output" / "reports" / "manuscript_staleness_report.json"
    for _ in range(2):
        variables = generate_variables(
            PROJECT_ROOT,
            require_analysis_outputs=not args.allow_draft,
        )
        out.write_text(json.dumps(variables, indent=2), encoding="utf-8")
        resolved_dir = write_resolved_manuscript(PROJECT_ROOT, variables)
        staleness_path = write_manuscript_staleness_report(PROJECT_ROOT)

    write_integration_audit_artifacts(PROJECT_ROOT)
    write_sheaf_track_artifacts(PROJECT_ROOT)
    compose_all_sections(PROJECT_ROOT)
    for _ in range(2):
        variables = generate_variables(
            PROJECT_ROOT,
            require_analysis_outputs=not args.allow_draft,
        )
        out.write_text(json.dumps(variables, indent=2), encoding="utf-8")
        resolved_dir = write_resolved_manuscript(PROJECT_ROOT, variables)
        staleness_path = write_manuscript_staleness_report(PROJECT_ROOT)
    semantic_paths = write_semantic_gluing_outputs(PROJECT_ROOT)
    print(out)
    for path in semantic_paths.values():
        print(path)
    print(resolved_dir)
    print(staleness_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
