"""Integration test for the figure-generation orchestrator (no mocks; real PNGs)."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT.parents[2]))

from infrastructure.validation.content.figure_validator import validate_figure_registry  # noqa: E402

SCRIPT_PATH = PROJECT_ROOT / "scripts" / "generate_figures.py"

EXPECTED_FIGURES = {
    "schema_overview.png",
    "file_inventory.png",
    "provenance_flow.png",
    "quality_gate.png",
    "checksum_verification.png",
}


def _load_script_module():
    spec = importlib.util.spec_from_file_location("generate_figures", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestGenerateFigures:
    """The thin script renders real PNG figures from the fixture descriptor."""

    def test_writes_all_figures_to_temp_root(self, tmp_path: Path) -> None:
        shutil.copytree(PROJECT_ROOT / "data", tmp_path / "data")
        module = _load_script_module()

        written = module.generate_figures(project_root=tmp_path)

        assert {path.name for path in written} == EXPECTED_FIGURES
        for path in written:
            assert path.is_file()
            assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
            assert path.parent == tmp_path / "manuscript" / "figures"

    def test_figures_are_non_empty_and_five(self, tmp_path: Path) -> None:
        shutil.copytree(PROJECT_ROOT / "data", tmp_path / "data")
        module = _load_script_module()

        written = module.generate_figures(project_root=tmp_path)

        assert len(written) == 5
        assert all(path.stat().st_size > 0 for path in written)

    def test_full_asset_pipeline_writes_valid_output_registry(self, tmp_path: Path) -> None:
        shutil.copytree(PROJECT_ROOT / "data", tmp_path / "data")
        shutil.copytree(PROJECT_ROOT / "manuscript", tmp_path / "manuscript")
        module = _load_script_module()

        written = module.main(project_root=tmp_path)

        registry = tmp_path / "output" / "figures" / "figure_registry.json"
        assert registry in written
        payload = json.loads(registry.read_text(encoding="utf-8"))
        assert {record["label"] for record in payload["figures"]} == {
            "fig:schema_overview",
            "fig:file_inventory",
            "fig:provenance_flow",
            "fig:quality_gate",
            "fig:checksum_verification",
        }
        ok, issues = validate_figure_registry(registry, tmp_path / "manuscript")
        assert ok, issues

    def test_incomplete_render_set_cannot_publish_registry(self, tmp_path: Path) -> None:
        shutil.copytree(PROJECT_ROOT / "data", tmp_path / "data")
        module = _load_script_module()
        rendered = module.generate_figures(project_root=tmp_path)
        output_figures = tmp_path / "output" / "figures"

        with pytest.raises(ValueError, match="missing generated figure file"):
            module.publish_generated_figures(
                output_figures,
                module.dd.DESCRIPTOR_FIGURE_SPECS,
                rendered[:-1],
                schema_version=module.dd.FIGURE_REGISTRY_SCHEMA,
            )

        assert not output_figures.exists()

    def test_validator_rejects_deleted_registered_figure(self, tmp_path: Path) -> None:
        shutil.copytree(PROJECT_ROOT / "data", tmp_path / "data")
        shutil.copytree(PROJECT_ROOT / "manuscript", tmp_path / "manuscript")
        module = _load_script_module()
        module.main(project_root=tmp_path)
        (tmp_path / "output" / "figures" / "quality_gate.png").unlink()

        ok, issues = validate_figure_registry(
            tmp_path / "output" / "figures" / "figure_registry.json",
            tmp_path / "manuscript",
        )

        assert not ok
        assert issues == ["Registered generated figure file is missing for fig:quality_gate: quality_gate.png"]
