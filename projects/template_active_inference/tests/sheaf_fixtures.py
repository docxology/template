"""Shared helpers for sheaf compose CLI tests."""

from __future__ import annotations

from pathlib import Path


def write_cli_fixture_project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    sheaf_dir = root / "manuscript" / "sheaf"
    section_dir = root / "manuscript" / "sections" / "demo"
    sheaf_dir.mkdir(parents=True)
    section_dir.mkdir(parents=True)
    (section_dir / "prose.md").write_text("Demo body", encoding="utf-8")
    (root / "figures.yaml").write_text(
        """
figures:
  sheaf_coverage_heatmap:
    filename: sheaf_coverage_heatmap.png
    alt: Coverage matrix
    caption: Coverage matrix.
section_figures:
  coverage_page:
    - id: sheaf_coverage_heatmap
      caption_prefix: "Coverage overview. "
""",
        encoding="utf-8",
    )
    (sheaf_dir / "tracks.yaml").write_text(
        """
tracks:
  prose:
    order: 1
    renderer: markdown
  optional:
    order: 2
    renderer: markdown
    optional: true
renderers:
  markdown:
    suffixes: [".md"]
""",
        encoding="utf-8",
    )
    (sheaf_dir / "manifest.yaml").write_text(
        """
sections:
  - id: demo
    order: 1
    title: Demo
    output_name: 01_demo.md
    tracks:
      prose: manuscript/sections/demo/prose.md
""",
        encoding="utf-8",
    )
    return root
