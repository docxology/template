"""Integration tests for the registry-backed figure publishing script."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT.parents[2]))

from infrastructure.validation.content.figure_validator import (  # noqa: E402
    validate_figure_registry,
)

from template_pools_rules_tools.figures.figures import (  # noqa: E402
    COVER_FIGURE_FILENAMES,
    INTEGRATION_FIGURE_SPECS,
    all_figures,
)

SCRIPT = PROJECT_ROOT / "scripts" / "05_generate_figures.py"


def _load_script_module(script: Path = SCRIPT):
    spec = importlib.util.spec_from_file_location("pools_rules_tools_generate_figures", script)
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
        spec.label for spec in INTEGRATION_FIGURE_SPECS
    }
    assert all(record["metadata"]["alt_text"] for record in payload["figures"])
    ok, issues = validate_figure_registry(registry, manuscript)
    assert ok, issues
    ok, issues = validate_figure_registry(registry, manuscript, require_accessibility=True)
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


def test_default_generation_preserves_manuscript_source_bytes(tmp_path: Path) -> None:
    project = tmp_path / "project"
    manuscript = project / "manuscript"
    shutil.copytree(PROJECT_ROOT / "manuscript", manuscript)
    script = project / "scripts" / SCRIPT.name
    script.parent.mkdir()
    shutil.copy2(SCRIPT, script)
    before = {
        path.relative_to(manuscript).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in manuscript.rglob("*")
        if path.is_file()
    }

    # Load the real entry point from an owned project so its actual default
    # destinations are exercised without writing in the repository checkout.
    module = _load_script_module(script)
    written = module.generate_assets()

    assert {
        path.relative_to(manuscript).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in manuscript.rglob("*")
        if path.is_file()
    } == before
    output = project / "output" / "figures"
    assert all(path.is_relative_to(output) for path in written)
    assert {path.name for path in output.glob("*.png")} == {
        *(spec.filename for spec in INTEGRATION_FIGURE_SPECS),
        *COVER_FIGURE_FILENAMES,
    }
    registry = output / "figure_registry.json"
    assert registry in written
    ok, issues = validate_figure_registry(registry, manuscript, require_accessibility=True)
    assert ok, issues
