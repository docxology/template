"""Shared green-project and validation-report builders for rendered-provenance tests."""

from __future__ import annotations
import json
from pathlib import Path
from infrastructure.core.pipeline.artifacts import snapshot_current_artifact_manifest
from infrastructure.rendering.manuscript_composition import write_manuscript_composition
from infrastructure.validation.rendered_snapshot import build_current_rendered_snapshot
from infrastructure.validation.output.validator import collect_detailed_validation_results
from tests._support.projects import make_project, write_doc

PROJECT = "templates/template_test"


def _write_green_validation_report(root: Path, project: Path) -> dict[str, object]:
    snapshot = build_current_rendered_snapshot(root, PROJECT)
    checks = {"Rendered structure": True, "Artifact manifest": True}
    detailed_validation = collect_detailed_validation_results(project / "output", require_pdf=False)
    payload: dict[str, object] = {
        "timestamp": "2026-01-01T00:00:00Z",
        "checks": checks,
        "figure_issues": [],
        "output_statistics": {
            "inventory_mode": "stable-shippable-output-v1",
            "detailed_validation": detailed_validation,
        },
        "summary": {
            "total_checks": len(checks),
            "passed": len(checks),
            "failed": 0,
            "figure_issues_count": 0,
            "all_passed": True,
        },
        "recommendations": [],
        "validated_inputs": snapshot.validated_inputs_dict(),
    }
    write_doc(
        project / "output" / "reports" / "validation_report.json",
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
    )
    return payload


def _green_project(
    root: Path,
    *,
    hydrated: bool = True,
    composition_algorithm: str = "web-renderer-combine-v1",
) -> Path:
    project = make_project(
        root,
        "template_test",
        program="templates",
        with_manuscript=True,
        with_output=True,
    )
    write_doc(root / ".gitignore", "# synthetic release ignore policy\n")
    write_doc(root / "pyproject.toml", '[project]\nname = "synthetic-template"\n')
    write_doc(
        root / "infrastructure" / "core" / "pipeline" / "pipeline.yaml",
        "stages:\n  - name: Render\n    script: scripts/pipeline/stage_03_render.py\n",
    )
    write_doc(
        root / "infrastructure" / "research" / "runtime_prompt.md",
        "Render every canonical source.\n",
    )
    write_doc(
        root / "infrastructure" / "rendering" / "layout.template",
        "<main>{{ manuscript }}</main>\n",
    )
    write_doc(
        root / "infrastructure" / "validation" / "output" / "runtime_gate.py",
        "REQUIRE_CURRENT_OUTPUT = True\n",
    )
    write_doc(root / "scripts" / "__init__.py", '"""Runtime stage bootstrap."""\n')
    write_doc(root / "scripts" / "pipeline" / "stage_03_render.py", 'print("render")\n')
    write_doc(
        project / "manuscript" / "00_abstract.md",
        "# Abstract\n\nAuthoring token {{RESULT_COUNT}} is hydratable.\n",
    )
    write_doc(project / "manuscript" / "01_methods.md", "# Methods\n\nMethod source.\n")

    if hydrated:
        write_doc(
            project / "output" / "manuscript" / "00_abstract.md",
            "# Abstract\n\nThere were 7 results.\n",
        )
        write_doc(
            project / "output" / "manuscript" / "01_methods.md",
            "# Methods\n\nMethod source.\n",
        )
        rendered_inputs = sorted((project / "output" / "manuscript").glob("*.md"))
    else:
        rendered_inputs = sorted(path for path in (project / "manuscript").glob("*.md") if path.name != "config.yaml")

    combined = project / "output" / "web" / "_combined_manuscript.md"
    combined_text = "\n\n".join(path.read_text(encoding="utf-8").rstrip() for path in rendered_inputs) + "\n"
    write_doc(combined, combined_text)
    write_manuscript_composition(
        project,
        PROJECT,
        rendered_inputs,
        combined,
        algorithm=composition_algorithm,
    )
    write_doc(project / "output" / "data" / "result.json", '{"count": 7}\n')
    snapshot_current_artifact_manifest(project / "output")
    _write_green_validation_report(root, project)
    return project
