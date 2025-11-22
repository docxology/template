import pytest
from unittest.mock import MagicMock
from pathlib import Path
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.core import RenderManager

@pytest.fixture
def mock_config(tmp_path):
    config = RenderingConfig()
    config.output_dir = str(tmp_path / "output")
    config.pdf_dir = str(tmp_path / "output/pdf")
    config.slides_dir = str(tmp_path / "output/slides")
    config.web_dir = str(tmp_path / "output/web")
    config.latex_compiler = "mock_latex"
    config.pandoc_path = "mock_pandoc"
    return config

@pytest.fixture
def mock_manager(mock_config, mocker):
    mocker.patch("infrastructure.rendering.pdf_renderer.compile_latex")
    mocker.patch("infrastructure.rendering.slides_renderer.subprocess.run")
    mocker.patch("infrastructure.rendering.web_renderer.subprocess.run")
    return RenderManager(mock_config)

