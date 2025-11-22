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

def test_slides_renderer_beamer(mock_config, mocker, tmp_path):
    renderer = SlidesRenderer(mock_config)
    
    # Create a temporary markdown file
    test_md = tmp_path / "test.md"
    test_md.write_text("# Test Presentation\n\nSome content")
    
    # Mock subprocess.run to handle pandoc conversion
    # and create output PDF file for LaTeX compilation
    def mock_run(cmd, **kwargs):
        if isinstance(cmd, list) and len(cmd) > 0:
            cmd_str = " ".join(cmd)
            
            # Handle pandoc markdown to LaTeX conversion
            if "pandoc" in cmd_str:
                if "-o" in cmd:
                    output_idx = cmd.index("-o") + 1
                    output_file = Path(cmd[output_idx])
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    # Create minimal LaTeX file
                    output_file.write_text(r"\documentclass{beamer}" + "\n" + r"\begin{document}" + "\n" + r"\end{document}")
                return mocker.MagicMock(returncode=0, stderr="")
            
            # Handle LaTeX compilation - check for mock_latex command
            if "mock_latex" in cmd_str or "latex" in cmd_str:
                # Extract output directory and tex file from command
                output_dir = None
                tex_file = None
                
                for arg in cmd:
                    if str(arg).startswith("-output-directory="):
                        output_dir = Path(str(arg).split("=", 1)[1])
                    elif str(arg).endswith(".tex"):
                        tex_file = Path(arg)
                
                if output_dir and tex_file:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    pdf_file = output_dir / (tex_file.stem + ".pdf")
                    pdf_file.write_text("mock pdf content")
                
                return mocker.MagicMock(returncode=0, stderr="")
        
        return mocker.MagicMock(returncode=0, stderr="")
    
    mocker.patch("subprocess.run", side_effect=mock_run)
    
    result = renderer.render(test_md, format="beamer")
    
    assert str(result).endswith(".pdf")

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

