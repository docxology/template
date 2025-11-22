import pytest
import subprocess
from pathlib import Path
from unittest.mock import MagicMock
from infrastructure.rendering.latex_utils import compile_latex
from infrastructure.core.exceptions import CompilationError

def test_compile_latex_success(tmp_path, mocker):
    tex_file = tmp_path / "test.tex"
    tex_file.touch()
    output_dir = tmp_path / "out"
    
    # Mock subprocess
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0
    
    # Mock PDF creation
    def side_effect(*args, **kwargs):
        (output_dir / "test.pdf").touch()
        return mock_run.return_value
    mock_run.side_effect = side_effect
    
    result = compile_latex(tex_file, output_dir)
    assert result == output_dir / "test.pdf"
    assert mock_run.call_count == 2 # 2 passes

def test_compile_latex_missing_file(tmp_path):
    with pytest.raises(CompilationError, match="not found"):
        compile_latex(tmp_path / "missing.tex", tmp_path / "out")

def test_compile_latex_failure(tmp_path, mocker):
    tex_file = tmp_path / "test.tex"
    tex_file.touch()
    output_dir = tmp_path / "out"
    
    # Mock subprocess fail
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 1
    mock_run.return_value.stderr = "Error"
    
    with pytest.raises(CompilationError, match="compilation failed"):
        compile_latex(tex_file, output_dir)

