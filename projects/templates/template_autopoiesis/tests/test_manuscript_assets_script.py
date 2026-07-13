"""Integration tests for registry-backed manuscript asset generation."""

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

SCRIPT = PROJECT_ROOT / "scripts" / "01_generate_manuscript_assets.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("autopoiesis_manuscript_assets", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_coverage(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "files": {
                    str(PROJECT_ROOT / "src" / "grammar.py"): {"summary": {"percent_covered": 96.0}},
                    str(PROJECT_ROOT / "src" / "manuscript_figures.py"): {"summary": {"percent_covered": 93.0}},
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def test_generate_assets_writes_valid_registry_in_temp_tree(tmp_path: Path) -> None:
    module = _load_script_module()
    figures = tmp_path / "project" / "output" / "figures"
    manuscript = tmp_path / "project" / "manuscript"
    shutil.copytree(PROJECT_ROOT / "manuscript", manuscript)

    written = module.generate_assets(
        PROJECT_ROOT,
        figures_dir=figures,
        coverage_path=_write_coverage(tmp_path / "coverage_full.json"),
    )

    assert {path.name for path in written} == {
        "fig_stacked_product.png",
        "fig_domain_coverage.png",
        "fig_product_space.png",
        "fig_coverage_by_module.png",
        "figure_registry.json",
    }
    registry = figures / "figure_registry.json"
    payload = json.loads(registry.read_text(encoding="utf-8"))
    assert {record["label"] for record in payload["figures"]} == {
        "fig:stacked_product",
        "fig:domain_coverage",
        "fig:product_space",
        "fig:coverage_by_module",
    }
    ok, issues = validate_figure_registry(registry, manuscript)
    assert ok, issues


def test_generate_assets_requires_real_coverage_input(tmp_path: Path) -> None:
    module = _load_script_module()
    figures = tmp_path / "output" / "figures"

    with pytest.raises(FileNotFoundError, match="required per-module coverage input"):
        module.generate_assets(
            PROJECT_ROOT,
            figures_dir=figures,
            coverage_path=tmp_path / "missing-coverage.json",
        )

    assert not (figures / "figure_registry.json").exists()


def test_validator_rejects_deleted_registered_figure(tmp_path: Path) -> None:
    module = _load_script_module()
    figures = tmp_path / "project" / "output" / "figures"
    manuscript = tmp_path / "project" / "manuscript"
    shutil.copytree(PROJECT_ROOT / "manuscript", manuscript)
    module.generate_assets(
        PROJECT_ROOT,
        figures_dir=figures,
        coverage_path=_write_coverage(tmp_path / "coverage_full.json"),
    )
    (figures / "fig_product_space.png").unlink()

    ok, issues = validate_figure_registry(figures / "figure_registry.json", manuscript)

    assert not ok
    assert issues == ["Registered generated figure file is missing for fig:product_space: fig_product_space.png"]
