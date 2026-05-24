"""Tests for infrastructure.rendering.core.RenderManager — coverage."""

import pytest

from infrastructure.core.exceptions import TemplateError
from infrastructure.rendering.core import RenderManager
from infrastructure.rendering.config import RenderingConfig


class TestRenderManagerInit:
    def test_default_init(self):
        rm = RenderManager()
        assert rm.config is not None
        assert rm.manuscript_dir is None
        assert rm.figures_dir is None

    def test_custom_init(self, tmp_path):
        config = RenderingConfig(pandoc_path="pandoc")
        manuscript_dir = tmp_path / "manuscript"
        figures_dir = tmp_path / "figures"
        manuscript_dir.mkdir()
        figures_dir.mkdir()
        rm = RenderManager(config=config, manuscript_dir=manuscript_dir, figures_dir=figures_dir)
        assert rm.manuscript_dir == manuscript_dir
        assert rm.figures_dir == figures_dir


class TestRenderAll:
    def test_file_not_exists(self, tmp_path):
        rm = RenderManager()
        with pytest.raises(TemplateError, match="does not exist"):
            rm.render_all(tmp_path / "nonexistent.md")

    def test_unsupported_format(self, tmp_path):
        source = tmp_path / "file.docx"
        source.write_text("content")
        rm = RenderManager()
        with pytest.raises(TemplateError, match="Unsupported file format"):
            rm.render_all(source)

    def test_unsupported_extension_txt(self, tmp_path):
        source = tmp_path / "file.txt"
        source.write_text("content")
        rm = RenderManager()
        with pytest.raises(TemplateError, match="Unsupported"):
            rm.render_all(source)
