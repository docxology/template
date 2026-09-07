"""Tests for infrastructure.rendering._combined_exports — branch coverage.

Covers fixture-driven branches for:
- combined_source_files: existing/missing path, transmission-bookend classification
- resolve_combined_markdown: manuscript/output dir layout, pdf/tex candidates, empty/missing
- resolve_bibliography: deterministic union, path deduplication, and conflicts
- render_combined_docx: no combined-md early return; bibliography/crossref/metadata paths
- render_combined_epub: no combined-md early return; bibliography present vs absent
- render_combined_outputs: enable_* toggles; RenderingError and OSError paths
"""

from __future__ import annotations

import json
from pathlib import Path


from infrastructure.transmission.transmission_bookends import BEGIN_FILENAME, END_FILENAME
from infrastructure.rendering._combined_exports import (
    combined_source_files,
    prepare_shared_combined_markdown,
    render_combined_outputs,
)
from ._combined_exports_helpers import _make_manager, _make_reporter


# ---------------------------------------------------------------------------
# combined_source_files
# ---------------------------------------------------------------------------


def test_combined_source_files_includes_existing_path(tmp_path: Path) -> None:
    """A file that exists on disk is always included regardless of bookend status."""
    existing = tmp_path / "01_intro.md"
    existing.write_text("# Intro\n")

    result = combined_source_files([existing])

    assert result == [existing]


def test_combined_source_files_excludes_missing_bookend(tmp_path: Path) -> None:
    """A missing transmission bookend (by filename) is excluded from the output list."""
    missing_bookend = tmp_path / BEGIN_FILENAME
    # Do NOT create the file — it is missing AND is_transmission_bookend => exclude

    result = combined_source_files([missing_bookend])

    assert result == []


def test_prepare_shared_combined_markdown_supports_docs_manuscript_root(tmp_path: Path) -> None:
    """The shared producer writes to project output for docs/manuscript layouts."""

    manuscript_dir = tmp_path / "docs" / "manuscript"
    manuscript_dir.mkdir(parents=True)
    source = manuscript_dir / "01_intro.md"
    source.write_text("# Docs manuscript\n", encoding="utf-8")
    manager = _make_manager(tmp_path)

    result = prepare_shared_combined_markdown(
        manager,
        [source],
        manuscript_dir,
        "templates/docs_project",
    )

    assert result == tmp_path / "output" / "web" / "_combined_manuscript.md"
    assert result.is_file()
    assert (tmp_path / "output" / "reports" / "manuscript_composition.json").is_file()


def test_slides_only_combined_stage_writes_current_composition_evidence(tmp_path: Path) -> None:
    """Without HTML, a slides-only run still binds its current manuscript inputs."""

    manuscript_dir = tmp_path / "manuscript"
    manuscript_dir.mkdir()
    source = manuscript_dir / "01_intro.md"
    source.write_text("# Slides manuscript\n", encoding="utf-8")
    manager = _make_manager(
        tmp_path,
        enable_pdf=False,
        enable_html=False,
        enable_slides=True,
        enable_docx=False,
        enable_epub=False,
    )

    render_combined_outputs(
        manager,
        [source],
        manuscript_dir,
        "templates/slides_project",
        _make_reporter(tmp_path),
        rendered_count=1,
    )

    combined = tmp_path / "output" / "web" / "_combined_manuscript.md"
    receipt = json.loads((tmp_path / "output" / "reports" / "manuscript_composition.json").read_text())
    assert combined.is_file()
    assert receipt["algorithm"] == "shared-combined-markdown-v1"


def test_combined_source_files_includes_missing_non_bookend(tmp_path: Path) -> None:
    """A missing non-bookend file is still included (caller is responsible for it)."""
    missing_regular = tmp_path / "05_discussion.md"
    # Do NOT create the file — missing AND NOT is_transmission_bookend => include

    result = combined_source_files([missing_regular])

    assert result == [missing_regular]


def test_combined_source_files_mixed_list(tmp_path: Path) -> None:
    """Mixed list: existing, missing-regular, and missing-bookend handled correctly."""
    existing = tmp_path / "01_intro.md"
    existing.write_text("# Intro\n")
    missing_regular = tmp_path / "02_methods.md"
    missing_end_bookend = tmp_path / END_FILENAME  # missing

    result = combined_source_files([existing, missing_regular, missing_end_bookend])

    assert existing in result
    assert missing_regular in result
    assert missing_end_bookend not in result
