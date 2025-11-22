import pytest
from pathlib import Path
from infrastructure.rendering.core import RenderManager

def test_render_all_tex(mock_manager, mocker):
    # Mock PDF renderer
    mock_manager.pdf_renderer.render = mocker.MagicMock(return_value=Path("out.pdf"))
    
    results = mock_manager.render_all(Path("test.tex"))
    assert len(results) == 1
    assert results[0] == Path("out.pdf")

def test_render_all_md(mock_manager, mocker):
    # Mock renderers
    mock_manager.slides_renderer.render = mocker.MagicMock(return_value=Path("out_slides.pdf"))
    mock_manager.web_renderer.render = mocker.MagicMock(return_value=Path("out.html"))
    
    results = mock_manager.render_all(Path("test.md"))
    assert len(results) == 2
    assert Path("out_slides.pdf") in results
    assert Path("out.html") in results

