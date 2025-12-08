import pytest
import shutil
from pathlib import Path
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.core import RenderManager


@pytest.fixture
def mock_config(tmp_path):
    """Create rendering config for tests using temp directories."""
    config = RenderingConfig()
    config.output_dir = str(tmp_path / "output")
    config.pdf_dir = str(tmp_path / "output/pdf")
    config.slides_dir = str(tmp_path / "output/slides")
    config.web_dir = str(tmp_path / "output/web")
    
    # Use real LaTeX compiler if available
    if shutil.which("xelatex"):
        config.latex_compiler = "xelatex"
    elif shutil.which("pdflatex"):
        config.latex_compiler = "pdflatex"
    else:
        config.latex_compiler = None
    
    # Use real pandoc if available
    config.pandoc_path = "pandoc" if shutil.which("pandoc") else None
    
    return config


@pytest.fixture
def render_manager(mock_config):
    """Create RenderManager for tests without mocking."""
    return RenderManager(mock_config)

