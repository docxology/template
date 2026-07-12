"""Integration tests for registered-report figure publication provenance."""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "generate_figures.py"
FIGURE_LABEL_RE = re.compile(r"\{#(fig:[A-Za-z0-9_:-]+)\}")


def _validate_registry(registry_path: Path, manuscript_dir: Path) -> tuple[bool, list[str]]:
    """Validate this exemplar's registry without monorepo-only dependencies."""
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    records = {str(record["label"]): record for record in payload.get("figures", []) if isinstance(record, dict)}
    references: set[str] = set()
    for path in manuscript_dir.rglob("*.md"):
        if path.name not in {"AGENTS.md", "README.md"}:
            references.update(FIGURE_LABEL_RE.findall(path.read_text(encoding="utf-8")))

    issues = [f"Unregistered figure reference: {label}" for label in sorted(references - set(records))]
    for label in sorted(references & set(records)):
        filename = records[label].get("filename")
        if isinstance(filename, str) and filename and not (registry_path.parent / filename).is_file():
            issues.append(f"Registered generated figure file is missing for {label}: {filename}")
    return not issues, issues


def _load_script_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("registered_report_generate_figures", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _copy_project_inputs(tmp_path: Path) -> tuple[Path, Path]:
    project = tmp_path / "project"
    shutil.copytree(PROJECT_ROOT / "data", project / "data")
    shutil.copytree(PROJECT_ROOT / "manuscript", project / "manuscript")
    return project, project / "data" / "example_registration.json"


def test_generate_assets_writes_validator_compatible_registry(tmp_path: Path) -> None:
    module = _load_script_module()
    project, registration = _copy_project_inputs(tmp_path)

    written, summary = module.generate_assets(
        registration,
        project / "manuscript" / "figures",
        project / "output" / "figures",
        project / "output" / "data",
    )

    registry = project / "output" / "figures" / "figure_registry.json"
    payload = json.loads(registry.read_text(encoding="utf-8"))
    assert registry in written
    assert summary["significant"] is True
    assert {record["label"] for record in payload["figures"]} == {
        "fig:hypothesis_map",
        "fig:analysis_dag",
        "fig:deviation_timeline",
        "fig:permutation_result",
    }
    ok, issues = _validate_registry(registry, project / "manuscript")
    assert ok, issues


def test_incomplete_render_set_cannot_publish_registry(tmp_path: Path) -> None:
    module = _load_script_module()
    project, registration_path = _copy_project_inputs(tmp_path)
    registration = cast(
        "dict[str, Any]",
        json.loads(registration_path.read_text(encoding="utf-8")),
    )
    frozen = module.freeze_registration(registration)
    summary = module.run_registered_analysis(frozen)
    figures = module.render_all_figures(frozen, summary, project / "canonical")
    figures.pop("analysis_dag")
    output = project / "output" / "figures"

    with pytest.raises(ValueError, match="missing generated figure file.*analysis_dag.png"):
        module.publish_output_figures(figures, output)

    assert not output.exists()


def test_validator_rejects_deleted_registered_figure(tmp_path: Path) -> None:
    module = _load_script_module()
    project, registration = _copy_project_inputs(tmp_path)
    module.generate_assets(
        registration,
        project / "manuscript" / "figures",
        project / "output" / "figures",
        project / "output" / "data",
    )
    (project / "output" / "figures" / "deviation_timeline.png").unlink()

    ok, issues = _validate_registry(
        project / "output" / "figures" / "figure_registry.json",
        project / "manuscript",
    )

    assert not ok
    assert issues == ["Registered generated figure file is missing for fig:deviation_timeline: deviation_timeline.png"]
