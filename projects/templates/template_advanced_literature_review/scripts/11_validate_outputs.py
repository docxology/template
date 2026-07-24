#!/usr/bin/env python3
"""Write deterministic evidence and artifact reports for the advanced exemplar."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from _bootstrap import bootstrap_project

PROJECT_ROOT = bootstrap_project(include_infrastructure=True)

from infrastructure.core.pipeline.artifacts import (
    snapshot_current_artifact_manifest,
    validate_artifact_manifest,
)
from infrastructure.project.discovery import resolve_project_root
from infrastructure.validation.content.figure_validator import validate_figure_registry
from infrastructure.validation.evidence_registry import (
    build_project_evidence_registry,
    write_evidence_registry_report,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project",
        default="templates/template_advanced_literature_review",
        help="Qualified project name under projects/.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = next(
        (parent for parent in (PROJECT_ROOT, *PROJECT_ROOT.parents) if (parent / "infrastructure").is_dir()),
        PROJECT_ROOT,
    )
    project_root = PROJECT_ROOT if repo_root == PROJECT_ROOT else resolve_project_root(repo_root, args.project)
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = snapshot_current_artifact_manifest(output_dir)
    manifest_report = validate_artifact_manifest(manifest, project_dir=project_root)

    registry = build_project_evidence_registry(project_root)
    evidence_path = write_evidence_registry_report(output_dir, registry)

    figure_path = output_dir / "figures" / "figure_registry.json"
    figure_ok = True
    figure_issues: list[str] = []
    if figure_path.exists():
        figure_ok, figure_issues = validate_figure_registry(figure_path, project_root / "manuscript")

    cross_phase_path = output_dir / "data" / "cross_phase_analysis.json"
    cross_phase_ok = False
    cross_phase_issues: list[str] = []
    if cross_phase_path.exists():
        try:
            cross_phase = json.loads(cross_phase_path.read_text(encoding="utf-8"))
            required = {"schema_version", "phase_order", "phase_membership", "citation_validation"}
            missing = sorted(required.difference(cross_phase)) if isinstance(cross_phase, dict) else sorted(required)
            if missing:
                cross_phase_issues.append(f"missing keys: {', '.join(missing)}")
            elif cross_phase.get("schema_version") != "advanced-literature-review/cross-phase-analysis/1":
                cross_phase_issues.append("unexpected schema_version")
            else:
                cross_phase_ok = True
        except (OSError, json.JSONDecodeError) as exc:
            cross_phase_issues.append(f"invalid JSON: {exc}")
    else:
        cross_phase_issues.append("cross_phase_analysis.json is missing")

    reports_dir = output_dir / "reports"
    payload = {
        "schema_version": "advanced-literature-review-validation-v1",
        "project": args.project,
        "checks": {
            "artifact_manifest": manifest_report.valid,
            "evidence_registry": evidence_path.exists(),
            "figure_registry": figure_ok,
            "cross_phase_analysis": cross_phase_ok,
        },
        "manifest_issues": list(manifest_report.issues),
        "figure_issues": figure_issues,
        "cross_phase_issues": cross_phase_issues,
        "status": "pass" if manifest_report.valid and figure_ok and cross_phase_ok else "fail",
    }
    report_path = reports_dir / "validation_report.json"
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (reports_dir / "validation_report.md").write_text(
        "# Advanced literature-review validation\n\n"
        f"Status: **{payload['status']}**\n\n"
        + "\n".join(f"- {name}: `{value}`" for name, value in payload["checks"].items())
        + "\n",
        encoding="utf-8",
    )
    print(report_path)
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
