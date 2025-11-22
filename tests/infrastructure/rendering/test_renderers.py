import pytest
import subprocess
from pathlib import Path
from infrastructure.rendering.pdf_renderer import PDFRenderer
from infrastructure.rendering.slides_renderer import SlidesRenderer
from infrastructure.rendering.web_renderer import WebRenderer
from infrastructure.core.exceptions import RenderingError

def test_pdf_renderer(mock_config, mocker):
    renderer = PDFRenderer(mock_config)
    mock_compile = mocker.patch("infrastructure.rendering.pdf_renderer.compile_latex")
    mock_compile.return_value = Path("out.pdf")
    
    result = renderer.render(Path("test.tex"))
    assert result == Path("out.pdf")
    mock_compile.assert_called_once()

def test_slides_renderer_beamer(mock_config, mocker):
    renderer = SlidesRenderer(mock_config)
    mock_run = mocker.patch("subprocess.run")
    
    result = renderer.render(Path("test.md"), format="beamer")
    
    assert str(result).endswith(".pdf")
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "-t" in args
    assert "beamer" in args

def test_web_renderer(mock_config, mocker):
    renderer = WebRenderer(mock_config)
    mock_run = mocker.patch("subprocess.run")
    
    result = renderer.render(Path("test.md"))
    
    assert str(result).endswith(".html")
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "-t" in args
    assert "html5" in args

def test_renderer_failure(mock_config, mocker):
    renderer = WebRenderer(mock_config)
    mocker.patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd", stderr="Error"))
    
    with pytest.raises(RenderingError):
        renderer.render(Path("test.md"))

