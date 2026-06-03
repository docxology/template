"""Documentation contract checks for reproducibility-facing references."""

from __future__ import annotations

from pathlib import Path


def test_rendering_reproducibility_reference_is_signposted(project_root: Path) -> None:
    docs_readme = (project_root / "docs" / "README.md").read_text(encoding="utf-8")
    project_readme = (project_root / "README.md").read_text(encoding="utf-8")
    reference = project_root / "docs" / "reference" / "rendering-reproducibility.md"

    assert "rendering-reproducibility.md" in docs_readme
    assert "rendering-reproducibility.md" in project_readme
    assert reference.is_file()

    text = reference.read_text(encoding="utf-8")
    for phrase in (
        "single hydration boundary",
        "Generated artifacts",
        "Authored surfaces",
        "Root output parity",
        "Figure rendering contract",
    ):
        assert phrase in text
