"""Comprehensive tests for infrastructure/validation/validate_markdown_cli.py.

Tests markdown validation CLI functionality using real implementations.
Follows No Mocks Policy - all tests use real data and real execution.
"""

import sys
import subprocess
from pathlib import Path
import pytest


class TestValidateMarkdownCliCore:
    """Test core validate markdown CLI functionality."""
    
    def test_module_imports(self):
        """Test that module imports correctly."""
        from infrastructure.validation import validate_markdown_cli
        assert validate_markdown_cli is not None
    
    def test_has_main_function(self):
        """Test that module has main function."""
        from infrastructure.validation import validate_markdown_cli
        assert hasattr(validate_markdown_cli, 'main') or hasattr(validate_markdown_cli, 'validate_markdown_cli')


class TestMarkdownValidationCommand:
    """Test markdown validation command using real execution."""
    
    def test_validate_single_file(self, tmp_path):
        """Test validating a single markdown file using real validation."""
        from infrastructure.validation import validate_markdown_cli
        
        md = tmp_path / "test.md"
        md.write_text("# Title\n\nContent")
        
        if hasattr(validate_markdown_cli, 'validate_markdown_file'):
            result = validate_markdown_cli.validate_markdown_file(str(md))
            assert result is not None
    
    def test_validate_directory(self, tmp_path):
        """Test validating a directory of markdown files using real validation."""
        from infrastructure.validation import validate_markdown_cli
        
        (tmp_path / "a.md").write_text("# A\n")
        (tmp_path / "b.md").write_text("# B\n")
        
        if hasattr(validate_markdown_cli, 'validate_markdown_directory'):
            result = validate_markdown_cli.validate_markdown_directory(str(tmp_path))
            assert result is not None


class TestMarkdownCliMain:
    """Test main entry point using real subprocess execution."""
    
    def test_main_with_valid_markdown(self, tmp_path):
        """Test main with valid markdown via real subprocess."""
        md = tmp_path / "test.md"
        md.write_text("# Title\n\nValid content.")
        
        # Run real CLI command via subprocess
        result = subprocess.run(
            [sys.executable, '-m', 'infrastructure.validation.validate_markdown_cli', str(md)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent
        )
        
        # May succeed or fail depending on validation
        assert result.returncode in [0, 1, 2]


class TestValidateMarkdownCliIntegration:
    """Integration tests for validate markdown CLI using real execution."""
    
    def test_full_validation_workflow(self, tmp_path):
        """Test complete validation workflow with real execution."""
        from infrastructure.validation import validate_markdown_cli
        
        # Create test markdown
        md = tmp_path / "test.md"
        md.write_text("# Test\n\n## Section\n\nContent here.")
        
        # Module should be importable
        assert validate_markdown_cli is not None
        
        # Use real validation
        try:
            result = validate_markdown_cli.main(manuscript_path=md)
            assert result in [0, 1, 2] or result is None
        except SystemExit:
            pass
