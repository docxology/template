"""Integration test for the figure-generation orchestrator (no mocks; real PNGs)."""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SCRIPT_PATH = PROJECT_ROOT / "scripts" / "generate_figures.py"
FIGURE_LABEL_RE = re.compile(r"\{#(fig:[A-Za-z0-9_:-]+)\}")

EXPECTED_FIGURES = {
    "schema_overview.png",
    "file_inventory.png",
    "provenance_flow.png",
    "quality_gate.png",
    "checksum_verification.png",
}


def _validate_registry(registry_path: Path, manuscript_dir: Path) -> tuple[bool, list[str]]:
    """Validate the standalone registry without importing monorepo packages."""
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
        ok, issues = _validate_registry(registry, tmp_path / "manuscript")
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

        ok, issues = _validate_registry(
            tmp_path / "output" / "figures" / "figure_registry.json",
            tmp_path / "manuscript",
        )

        assert not ok
        assert issues == ["Registered generated figure file is missing for fig:quality_gate: quality_gate.png"]
