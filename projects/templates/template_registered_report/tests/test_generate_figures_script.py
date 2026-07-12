"""Integration tests for registered-report figure publication provenance."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any, cast

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT.parents[2]))

from infrastructure.validation.content.figure_validator import validate_figure_registry  # noqa: E402

SCRIPT = PROJECT_ROOT / "scripts" / "generate_figures.py"


def _load_script_module():
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
    ok, issues = validate_figure_registry(registry, project / "manuscript")
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

    ok, issues = validate_figure_registry(
        project / "output" / "figures" / "figure_registry.json",
        project / "manuscript",
    )

    assert not ok
    assert issues == ["Registered generated figure file is missing for fig:deviation_timeline: deviation_timeline.png"]
