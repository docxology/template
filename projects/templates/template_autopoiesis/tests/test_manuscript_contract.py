"""Negative controls for the deterministic Phase 10 source contract."""

from __future__ import annotations

import shutil
from pathlib import Path

from src.manuscript_contract import REQUIRED_MANUSCRIPT_FILES, validate_phase10_contract


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _minimal_source_copy(source: Path, destination: Path) -> Path:
    """Copy only source-owned Phase 10 inputs into a disposable root."""
    (destination / "manuscript").mkdir(parents=True)
    for relative in REQUIRED_MANUSCRIPT_FILES:
        source_path = source / "manuscript" / relative
        target = destination / "manuscript" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target)
    shutil.copy2(source / "SPEC.md", destination / "SPEC.md")
    return destination


def test_phase10_source_contract_passes_for_public_exemplar() -> None:
    assert validate_phase10_contract(PROJECT_ROOT) == []


def test_phase10_contract_rejects_unfenced_preamble(tmp_path: Path) -> None:
    root = _minimal_source_copy(PROJECT_ROOT, tmp_path / "project")
    preamble = root / "manuscript" / "preamble.md"
    preamble.write_text(
        preamble.read_text(encoding="utf-8").replace("% END TEMPLATE_AUTOPOIESIS_PREAMBLE", ""),
        encoding="utf-8",
    )

    issues = validate_phase10_contract(root)

    assert any("exactly one" in issue for issue in issues)


def test_phase10_contract_rejects_geometry_override(tmp_path: Path) -> None:
    root = _minimal_source_copy(PROJECT_ROOT, tmp_path / "project")
    preamble = root / "manuscript" / "preamble.md"
    preamble.write_text(preamble.read_text(encoding="utf-8") + "\n\\geometry{margin=1in}\n", encoding="utf-8")

    issues = validate_phase10_contract(root)

    assert any("geometry" in issue for issue in issues)
