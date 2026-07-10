"""Integration test for the figure-generation orchestrator (no mocks; real PNGs)."""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
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
