"""Integration tests for the registry-backed figure publishing script."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT.parents[2]))

from infrastructure.validation.content.figure_validator import (  # noqa: E402
    validate_figure_registry,
)

from src.figures import all_figures  # noqa: E402

SCRIPT = PROJECT_ROOT / "scripts" / "05_generate_figures.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("pools_rules_tools_generate_figures", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generate_assets_writes_registry_for_real_integration_figures(tmp_path: Path) -> None:
    module = _load_script_module()
    project = tmp_path / "project"
    manuscript = project / "manuscript"
    shutil.copytree(PROJECT_ROOT / "manuscript", manuscript)

    written = module.generate_assets(
        figures_dir=manuscript / "figures",
        output_figures_dir=project / "output" / "figures",
    )

    registry = project / "output" / "figures" / "figure_registry.json"
    payload = json.loads(registry.read_text(encoding="utf-8"))
    assert registry in written
    assert {record["label"] for record in payload["figures"]} == {
        "fig:architecture",
        "fig:counts",
        "fig:pipeline",
        "fig:taxonomy",
        "fig:rulehier",
        "fig:toolcontract",
        "fig:resilience",
        "fig:pipelineflow",
    }
    ok, issues = validate_figure_registry(registry, manuscript)
    assert ok, issues


def test_incomplete_real_figure_set_cannot_be_published(tmp_path: Path) -> None:
    module = _load_script_module()
    figures = all_figures(output_dir=tmp_path / "canonical")
    assert figures is not None
    figures.pop("pipeline_flow")
    output = tmp_path / "output" / "figures"

    with pytest.raises(ValueError, match="missing generated figure file.*pipeline_flow.png"):
        module.publish_output_figures(figures, output)

    assert not output.exists()


def test_validator_rejects_deleted_published_figure(tmp_path: Path) -> None:
    module = _load_script_module()
    project = tmp_path / "project"
    manuscript = project / "manuscript"
    shutil.copytree(PROJECT_ROOT / "manuscript", manuscript)
    module.generate_assets(
        figures_dir=manuscript / "figures",
        output_figures_dir=project / "output" / "figures",
    )
    (project / "output" / "figures" / "rule_hierarchy.png").unlink()

    ok, issues = validate_figure_registry(
        project / "output" / "figures" / "figure_registry.json",
        manuscript,
    )

    assert not ok
    assert issues == [
        "Registered generated figure file is missing for fig:rulehier: rule_hierarchy.png"
    ]
