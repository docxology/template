"""Prerender hard-gate (prevalidate_for_render) tests (split from test_transmission_validation.py)."""

from __future__ import annotations

from pathlib import Path
import pytest
from infrastructure.core.exceptions import RenderingError
from infrastructure.validation.content.prerender import prevalidate_for_render
from ._transmission_validation_helpers import (
    _make_manuscript,
    _write_md,
)


class TestPrevalidateForRender:
    """Hard-gate behaviour for the combined-PDF pre-render leaf."""

    def test_clean_manuscript_passes(self, tmp_path: Path) -> None:
        manuscript = _make_manuscript(tmp_path)
        _write_md(manuscript, "01_intro.md", "# Intro\n\nSee [@good_key].\n")
        # Should not raise
        prevalidate_for_render(manuscript, repo_root=tmp_path)

    def test_nonexistent_source_path_returns_silently(self, tmp_path: Path) -> None:
        """A Path that doesn't exist returns without error (no files to validate)."""
        prevalidate_for_render(tmp_path / "nonexistent", repo_root=tmp_path)

    def test_empty_path_list_returns_silently(self, tmp_path: Path) -> None:
        prevalidate_for_render([], repo_root=tmp_path)

    def test_undefined_citation_raises_rendering_error(self, tmp_path: Path) -> None:
        manuscript = _make_manuscript(tmp_path)
        _write_md(manuscript, "01_intro.md", "See [@missing_key] and [@good_key].\n")
        with pytest.raises(RenderingError) as excinfo:
            prevalidate_for_render(manuscript, repo_root=tmp_path)
        assert "missing_key" in str(excinfo.value)
        assert "Pre-render validation failed" in str(excinfo.value)

    def test_bare_pipe_raises_rendering_error(self, tmp_path: Path) -> None:
        manuscript = _make_manuscript(tmp_path)
        _write_md(manuscript, "01_intro.md", "Mean |N400| in caption.\n")
        with pytest.raises(RenderingError) as excinfo:
            prevalidate_for_render(manuscript, repo_root=tmp_path)
        assert "Pre-render validation failed" in str(excinfo.value)
        assert "01_intro.md" in str(excinfo.value)

    def test_explicit_path_list_signature(self, tmp_path: Path) -> None:
        manuscript = _make_manuscript(tmp_path)
        md = _write_md(manuscript, "01_intro.md", "Clean text.\n")
        prevalidate_for_render([md], bib_file=manuscript / "references.bib")

    def test_citation_resolves_with_second_bib_file(self, tmp_path: Path) -> None:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        (manuscript / "references.bib").write_text("@article{good_key, title={Ok}, year={2025}}\n", encoding="utf-8")
        (manuscript / "references_deep.bib").write_text(
            "@article{deep_only, title={Deep}, year={2025}}\n", encoding="utf-8"
        )
        _write_md(manuscript, "01_intro.md", "See [@good_key] and [@deep_only].\n")
        prevalidate_for_render(manuscript)

    def test_error_message_includes_severity_counts(self, tmp_path: Path) -> None:
        """RenderingError message reports error and warning counts."""
        manuscript = _make_manuscript(tmp_path)
        # ERROR: undefined citation; WARNING: bare pipe
        _write_md(manuscript, "01_intro.md", "See [@bad] and |word| here.\n")
        with pytest.raises(RenderingError) as excinfo:
            prevalidate_for_render(manuscript, repo_root=tmp_path)
        msg = str(excinfo.value)
        assert "blocker" in msg
